defmodule DataIngestionService.Workers.AwsCloudResources do
  @moduledoc """
  Oban worker that collects AWS S3 bucket metadata through the shared API client
  and forwards the normalized resources to the analysis service.
  """

  use Oban.Worker,
    queue: :default,
    max_attempts: 3,
    unique: [period: 300]

  require Logger

  alias DataIngestionService.ApiClient
  alias DataIngestionService.DataCollectorsCtx.AwsProvider
  alias DataIngestionService.Repo
  alias DataIngestionService.Schema.CloudAccount

  import Ecto.Query

  @impl Oban.Worker
  def perform(%Oban.Job{args: args}) do
    args = normalize_args(args)
    accounts = accounts_to_process(args)
    IO.inspect(accounts, label: "accounts3232")
    Enum.each(accounts, &process_account(&1, args))

    :ok
  end

  defp process_account(%CloudAccount{id: account_id} = account, args) do
    IO.inspect(account, label: "process_account3232")
    override_region = region_override(args)
    opts = maybe_region_option(override_region)
    region_label = override_region || account.region || default_region()

    Logger.info("Collecting AWS S3 resources for account=#{account_id} region=#{region_label}")

    case AwsProvider.fetch_all_buckets_metadata(account, opts) do
      {:ok, resources} ->
        Logger.info(
          "Collected #{length(resources)} bucket resource(s) for account=#{account_id} region=#{region_label}"
        )

        Logger.info(
          "Publishing #{length(resources)} resource(s) for analysis for account=#{account_id}"
        )

        ApiClient.send_for_analysis(resources) |> IO.inspect(label: "send_for_analysis3232")

      {:error, :missing_aws_credentials} ->
        Logger.warning(
          "AWS cloud resource worker skipped for account=#{account_id}: missing credentials"
        )

      {:error, reason} ->
        Logger.error(
          "AWS cloud resource worker failed for account=#{account_id} reason=#{inspect(reason)}"
        )
    end
  end

  defp accounts_to_process(args) do
    case account_id_from_args(args) do
      nil -> aws_accounts()
      id -> account_by_id(id)
    end
  end

  defp account_by_id(account_id) do
    CloudAccount
    |> where([a], a.is_active == true and a.id == ^account_id)
    |> Repo.one()
    |> case do
      nil -> []
      account -> [account]
    end
  end

  defp aws_accounts do
    CloudAccount
    |> where([a], a.is_active == true)
    |> Repo.all()
    |> Enum.filter(&(normalize_provider(&1.provider) == "AWS"))
  end

  defp account_id_from_args(args) do
    Map.get(args, "cloud_account_id") || Map.get(args, :cloud_account_id)
  end

  defp region_override(args) do
    Map.get(args, "region") || Map.get(args, :region)
  end

  defp maybe_region_option(nil), do: []
  defp maybe_region_option(region), do: [region: region]

  defp normalize_provider(nil), do: ""
  defp normalize_provider(provider) when is_binary(provider), do: provider |> String.upcase()
  defp normalize_provider(provider), do: provider |> to_string() |> String.upcase()

  defp default_region do
    Application.get_env(:data_ingestion_service, DataIngestionService.APIClient.Aws, [])
    |> Keyword.get(:region) || "eu-north-1"
  end

  defp normalize_args(args) when is_map(args), do: args
  defp normalize_args(_), do: %{}
end
