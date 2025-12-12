defmodule DataIngestionService.Application do
  @moduledoc false

  use Application

  @impl true
  def start(_type, _args) do
    kafka_enabled =
      Application.get_env(:data_ingestion_service, :enable_kafka, false)

    kafka_cfg = Application.get_env(:data_ingestion_service, :kafka, [])

    children =
      [
        DataIngestionService.Repo,
        {Finch, name: MyFinch},
        {Registry, keys: :unique, name: DataIngestionService.Registry},
        {DynamicSupervisor, strategy: :one_for_one, name: DataIngestionService.PollerSupervisor},
        DataIngestionService.Workers.CloudAccountWatcher
      ]
      |> Kernel.++(
        if kafka_enabled do
          _endpoints =
            case kafka_cfg do
              m when is_map(m) -> Map.get(m, :endpoints) || [{"localhost", 9092}]
              kw when is_list(kw) -> Keyword.get(kw, :endpoints, [{"localhost", 9092}])
              _ -> [{"localhost", 9092}]
            end

          _topic =
            case kafka_cfg do
              m when is_map(m) -> Map.get(m, :topic) || "cloud_audit_events"
              kw when is_list(kw) -> Keyword.get(kw, :topic, "cloud_audit_events")
              _ -> "cloud_audit_events"
            end

          [
            %{
              id: DataIngestionService.KafkaProducer,
              start: {DataIngestionService.KafkaProducer, :start_link, [[]]},
              type: :worker,
              restart: :permanent,
              shutdown: 5_000
            }
          ]
        else
          []
        end
      )
      |> Kernel.++([
        {Oban, Application.fetch_env!(:data_ingestion_service, Oban)}
      ])

    opts = [strategy: :one_for_one, name: DataIngestionService.Supervisor]
    Supervisor.start_link(children, opts)
  end
end
