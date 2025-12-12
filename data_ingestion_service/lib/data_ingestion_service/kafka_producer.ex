defmodule DataIngestionService.KafkaProducer do
  @moduledoc """
  GenServer-based Kafka producer for publishing audit events.
  """

  use GenServer
  require Logger

  @client :kafka_client

  @spec start_link(keyword()) :: GenServer.on_start()
  def start_link(opts \\ []) do
    GenServer.start_link(__MODULE__, opts, name: __MODULE__)
  end

  @doc """
  Publishes a list of events to Kafka synchronously via the GenServer.
  """
  @spec publish_events(list(any())) :: :ok | {:error, term()}
  def publish_events(events) when is_list(events) do
    GenServer.call(__MODULE__, {:publish_events, events}, 30_000)
  catch
    :exit, {:noproc, _} -> {:error, :producer_not_started}
  end

  @doc """
  Publishes a list of events to a specific Kafka topic.
  """
  @spec publish_events_to_topic(list(any()), String.t()) :: :ok | {:error, term()}
  def publish_events_to_topic(events, topic) when is_list(events) and is_binary(topic) do
    GenServer.call(__MODULE__, {:publish_events_to_topic, events, topic}, 30_000)
  catch
    :exit, {:noproc, _} -> {:error, :producer_not_started}
  end

  @impl true
  def init(_opts) do
    state = %{topic: topic(), enabled?: kafka_enabled?()}

    if state.enabled? do
      case :brod.start_client(endpoints(), @client, []) do
        :ok ->
          :ok

        {:error, {:already_started, _pid}} ->
          :ok

        {:error, reason} ->
          Logger.error(
            "Failed to start brod client in init reason=#{inspect(reason)} endpoints=#{inspect(endpoints())}"
          )
      end

      case :brod.start_producer(@client, state.topic, []) do
        :ok ->
          :ok

        {:error, {:already_started, _pid}} ->
          :ok

        {:error, reason} ->
          Logger.error(
            "Failed to start brod producer in init reason=#{inspect(reason)} topic=#{state.topic}"
          )
      end
    end

    {:ok, state}
  end

  @impl true
  def handle_call({:publish_events, events}, _from, %{enabled?: false} = state) do
    Logger.info("Kafka is disabled; skipping publish of #{length(events)} event(s)")
    {:reply, :ok, state}
  end

  def handle_call({:publish_events_to_topic, events, _topic}, _from, %{enabled?: false} = state) do
    Logger.info("Kafka is disabled; skipping publish of #{length(events)} event(s)")
    {:reply, :ok, state}
  end

  def handle_call({:publish_events, events}, _from, %{topic: topic} = state) do
    case wait_until_ready(@client, topic, 5, 200) do
      :ok ->
        result = do_publish(@client, topic, events)
        {:reply, result, state}

      {:error, reason} ->
        Logger.error("Kafka not ready; failed before publish reason=#{inspect(reason)}")
        {:reply, {:error, reason}, state}
    end
  end

  def handle_call({:publish_events_to_topic, events, topic}, _from, state) do
    _ = ensure_producer_started(topic)

    case wait_until_ready(@client, topic, 5, 200) do
      :ok ->
        result = do_publish(@client, topic, events)
        {:reply, result, state}

      {:error, reason} ->
        Logger.error("Kafka not ready; failed before publish reason=#{inspect(reason)}")
        {:reply, {:error, reason}, state}
    end
  end

  defp kafka_enabled? do
    Application.get_env(:data_ingestion_service, :enable_kafka, false)
  end

  defp endpoints do
    case Application.get_env(:data_ingestion_service, :kafka) do
      %{endpoints: eps} when is_list(eps) -> eps
      kw when is_list(kw) -> Keyword.get(kw, :endpoints, [{"localhost", 9092}])
      _ -> [{"localhost", 9092}]
    end
  end

  defp topic do
    case Application.get_env(:data_ingestion_service, :kafka) do
      %{topic: topic} -> topic
      kw when is_list(kw) -> Keyword.get(kw, :topic, "cloud_audit_events")
      _ -> "cloud_audit_events"
    end
  end

  defp ensure_producer_started(topic) when is_binary(topic) do
    case :brod.start_producer(@client, topic, []) do
      :ok -> :ok
      {:error, {:already_started, _pid}} -> :ok
      {:error, _} -> :ok
    end
  end

  defp do_publish(client, topic, events) do
    result =
      Enum.reduce_while(events, :ok, fn event, _acc ->
        case Jason.encode(to_encodable(event)) do
          {:ok, json} ->
            case :brod.produce_sync(client, topic, :random, "", json) do
              :ok ->
                Logger.debug("Kafka produce succeeded topic=#{topic} bytes=#{byte_size(json)}")
                {:cont, :ok}

              {:error, reason} ->
                Logger.error("Kafka produce failed topic=#{topic} reason=#{inspect(reason)}")
                {:halt, {:error, reason}}
            end

          {:error, reason} ->
            Logger.error("Kafka payload encode failed reason=#{inspect(reason)}")
            {:halt, {:error, reason}}
        end
      end)

    case result do
      :ok ->
        Logger.info("Published #{length(events)} event(s) to Kafka topic #{topic}")
        :ok

      {:error, reason} ->
        Logger.error(
          "Failed to publish #{length(events)} event(s) to Kafka topic #{topic} reason=#{inspect(reason)}"
        )

        {:error, reason}
    end
  end

  defp to_encodable(%_{} = struct), do: Map.from_struct(struct)
  defp to_encodable(other), do: other

  defp wait_until_ready(_client, _topic, 0, _delay_ms), do: {:error, :not_ready}

  defp wait_until_ready(client, topic, attempts, delay_ms) when attempts > 0 do
    case :brod.get_partitions_count(client, topic) do
      {:ok, _n} ->
        :ok

      {:error, _} ->
        Process.sleep(delay_ms)
        wait_until_ready(client, topic, attempts - 1, delay_ms)
    end
  end
end
