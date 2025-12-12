defmodule DataIngestionService.Collector do
  use Oban.Worker,
    queue: :default,
    max_attempts: 5,
    unique: [period: 300]

  @impl Oban.Worker
  def perform(%Oban.Job{args: _args}) do
    case collect_and_send_data() do
      :ok -> :ok
      {:error, reason} -> {:error, reason}
    end
  end

  def enqueue_now(args \\ %{}) when is_map(args) do
    args
    |> __MODULE__.new()
    |> Oban.insert()
  end

  defp collect_and_send_data() do
    case DataIngestionService.DataCollectorsCtx.AwsProvider.fetch_all_buckets_metadata() do
      {:ok, buckets_data} ->
        DataIngestionService.ApiClient.send_for_analysis(buckets_data)
        :ok

      {:error, reason} ->
        {:error, reason}
    end
  end
end
