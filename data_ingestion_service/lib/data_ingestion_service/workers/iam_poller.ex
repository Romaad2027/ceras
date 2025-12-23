defmodule DataIngestionService.Workers.IamPoller do
  @moduledoc """
  Oban worker that polls AWS IAM identities for each registered AWS cloud account.
  """

  use Oban.Worker,
    queue: :iam,
    max_attempts: 3,
    unique: [period: :timer.minutes(1)]

  require Logger

  alias DataIngestionService.KafkaProducer
  alias DataIngestionService.Providers.IamProvider
  alias DataIngestionService.Repo
  alias DataIngestionService.Schema.CloudAccount

  @topic "cloud_identities"

  @impl Oban.Worker
  def perform(%Oban.Job{}) do
    Logger.info("IAM poller started")

    aws_accounts()
    |> Enum.each(&poll_account/1)

    Logger.info("IAM poller finished")

    :ok
  end

  defp aws_accounts do
    import Ecto.Query

    CloudAccount
    |> where([a], a.is_active == true)
    |> Repo.all()
    |> IO.inspect(label: "aws_accounts")
    |> Enum.filter(&(normalize_provider(&1.provider) == "AWS"))
  end

  defp poll_account(%CloudAccount{
         id: account_id,
         credentials: creds,
         region: region,
         organization_id: organization_id
       }) do
    aws_config = build_aws_config(creds, region)

    case aws_config do
      [] ->
        Logger.warning("Skipping IAM poll for account=#{account_id} due to missing credentials")

      _ ->
        Logger.info("Polling IAM for account=#{account_id}")
        fetch_identities(account_id, aws_config, organization_id)
    end
  end

  defp fetch_identities(account_id, aws_config, organization_id) do
    case IamProvider.fetch_identities(aws_config, organization_id) do
      {:ok, []} ->
        Logger.info("No IAM identities found for account=#{account_id}")
        :ok

      {:ok, identities} ->
        publish_identities(account_id, identities)

      {:error, reason} ->
        log_fetch_error(account_id, reason)
    end
  end

  defp publish_identities(account_id, identities) do
    IO.inspect(identities, label: "identities")

    case KafkaProducer.publish_events_to_topic(identities, @topic) do
      :ok ->
        Logger.info("Published #{length(identities)} IAM identities for account=#{account_id}")
        :ok

      {:error, reason} ->
        log_publish_error(account_id, reason)
    end
  end

  defp build_aws_config(creds, region) when is_map(creds) do
    [
      access_key_id: credential_value(creds, :accessKeyId),
      secret_access_key: credential_value(creds, :secretAccessKey),
      region: region
    ]
    |> Enum.reject(fn {_key, value} -> is_nil(value) end)
  end

  defp build_aws_config(_, _), do: []

  defp credential_value(creds, key_base) do
    credential_keys(key_base)
    |> Enum.find_value(fn key -> Map.get(creds, key) end)
  end

  defp credential_keys(base) when is_atom(base) do
    candidate = Atom.to_string(base)

    [candidate, "aws_#{candidate}"]
    |> Enum.flat_map(fn variant ->
      [String.to_atom(variant), variant]
    end)
  end

  defp credential_keys(_), do: []

  defp normalize_provider(nil), do: ""
  defp normalize_provider(provider) when is_binary(provider), do: String.upcase(provider)
  defp normalize_provider(provider), do: provider |> to_string() |> String.upcase()

  defp log_fetch_error(account_id, reason) do
    Logger.error("Failed to fetch IAM identities account=#{account_id} reason=#{inspect(reason)}")
  end

  defp log_publish_error(account_id, reason) do
    Logger.error(
      "Failed to publish IAM identities account=#{account_id} reason=#{inspect(reason)}"
    )
  end
end
