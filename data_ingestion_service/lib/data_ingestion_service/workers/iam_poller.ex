defmodule DataIngestionService.Workers.IamPoller do
  @moduledoc """
  GenServer that periodically polls AWS IAM identities and forwards them to Kafka for a given organization.
  """

  use GenServer

  alias DataIngestionService.KafkaProducer
  alias DataIngestionService.Providers.IamProvider

  @type state :: %{
          org: map(),
          interval_ms: non_neg_integer()
        }

  @default_interval_ms :timer.minutes(10)
  @topic "cloud_identities"

  @spec child_spec(map()) :: Supervisor.child_spec()
  def child_spec(org) when is_map(org) do
    org_id = org[:id] || org["id"]

    %{
      id: {:iam_poller, org_id},
      start: {__MODULE__, :start_link, [org]},
      restart: :permanent,
      shutdown: 5_000,
      type: :worker
    }
  end

  @spec start_link(map()) :: GenServer.on_start()
  def start_link(%{id: id} = org) when is_binary(id) do
    GenServer.start_link(__MODULE__, org, name: via_tuple(id))
  end

  def start_link(%{"id" => id} = org) when is_binary(id) do
    GenServer.start_link(__MODULE__, org, name: via_tuple(id))
  end

  @impl true
  @spec init(map()) :: {:ok, state()}
  def init(org) when is_map(org) do
    state = %{org: org, interval_ms: @default_interval_ms}
    Process.send_after(self(), :tick, 0)
    {:ok, state}
  end

  @impl true
  def handle_info(:tick, %{org: org, interval_ms: interval_ms} = state) do
    _ = fetch_and_publish(org)
    Process.send_after(self(), :tick, interval_ms)
    {:noreply, state}
  end

  defp via_tuple(org_id), do: {:via, Registry, {DataIngestionService.Registry, {:iam, org_id}}}

  defp fetch_and_publish(org) do
    aws_config = build_aws_config(org)

    case IamProvider.fetch_identities(aws_config) do
      {:ok, []} ->
        :ok

      {:ok, identities} ->
        KafkaProducer.publish_events_to_topic(identities, @topic)

      {:error, _reason} ->
        :error
    end
  end

  defp build_aws_config(org) when is_map(org) do
    [
      access_key_id: org[:aws_access_key_id] || org["aws_access_key_id"],
      secret_access_key: org[:aws_secret_access_key] || org["aws_secret_access_key"],
      region: org[:aws_region] || org["aws_region"]
    ]
  end
end
