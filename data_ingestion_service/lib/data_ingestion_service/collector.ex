defmodule DataIngestionService.Collector do
  use Oban.Worker,
    queue: :default,
    max_attempts: 5,
    unique: [period: 300]

  require Logger

  alias DataIngestionService.ApiClient
  alias DataIngestionService.DataCollectorsCtx.AwsProvider
  alias DataIngestionService.Repo
  alias DataIngestionService.Schema.CloudAccount

  import Ecto.Query

  @impl Oban.Worker
  def perform(%Oban.Job{args: _args}) do
    collect_and_send_data()
  end

  def enqueue_now(args \\ %{}) when is_map(args) do
    args
    |> __MODULE__.new()
    |> Oban.insert()
  end

  defp collect_and_send_data do
    aws_accounts()
    |> Enum.each(&collect_for_account/1)

    :ok
  end

  defp collect_for_account(%CloudAccount{id: account_id} = account) do
    case AwsProvider.fetch_all_buckets_metadata(account) do
      {:ok, buckets_data} ->
        ApiClient.send_for_analysis(buckets_data)

      {:error, :missing_aws_credentials} ->
        Logger.warning("Collector skipped AWS account=#{account_id}: missing credentials")

      {:error, reason} ->
        Logger.error("Collector failed for AWS account=#{account_id} reason=#{inspect(reason)}")
    end
  end

  defp aws_accounts do
    CloudAccount
    |> where([a], a.is_active == true)
    |> Repo.all()
    |> Enum.filter(&(normalize_provider(&1.provider) == "AWS"))
  end

  defp normalize_provider(nil), do: ""
  defp normalize_provider(provider) when is_binary(provider), do: provider |> String.upcase()
  defp normalize_provider(provider), do: provider |> to_string() |> String.upcase()
end
