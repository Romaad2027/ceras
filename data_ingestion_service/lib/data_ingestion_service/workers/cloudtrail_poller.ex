defmodule DataIngestionService.Workers.CloudtrailPoller do
  @moduledoc """
  GenServer that polls AWS CloudTrail for events and forwards them to Kafka for a given cloud account.
  """

  use GenServer

  alias DataIngestionService.GenericAuditEvent
  alias DataIngestionService.KafkaProducer
  alias DataIngestionService.Schema.CloudAccount
  alias ExAws.Operation.JSON, as: OpJSON

  @type state :: %{
          account: CloudAccount.t()
        }

  @spec child_spec(CloudAccount.t()) :: Supervisor.child_spec()
  def child_spec(%CloudAccount{id: id} = account) do
    %{
      id: {:cloudtrail_poller, id},
      start: {__MODULE__, :start_link, [account]},
      restart: :permanent,
      shutdown: 5_000,
      type: :worker
    }
  end

  @spec start_link(CloudAccount.t()) :: GenServer.on_start()
  def start_link(%CloudAccount{id: id} = account) when is_binary(id) do
    GenServer.start_link(__MODULE__, account, name: via_tuple(id))
  end

  @impl true
  @spec init(CloudAccount.t()) :: {:ok, state(), {:continue, :poll}}
  def init(%CloudAccount{} = account) do
    state = %{account: account}
    {:ok, state, {:continue, :poll}}
  end

  @impl true
  def handle_continue(:poll, state) do
    since =
      DateTime.utc_now()
      |> DateTime.add(-10, :hour)
      |> DateTime.truncate(:second)

    _ = fetch_and_process(since, state)
    {:noreply, state}
  end

  @spec poll_now(GenServer.server(), non_neg_integer()) :: :ok
  def poll_now(server, lookback_seconds \\ 600) do
    GenServer.cast(server, {:poll, lookback_seconds})
  end

  @impl true
  def handle_cast({:poll, lookback_seconds}, state) when is_integer(lookback_seconds) do
    since =
      DateTime.utc_now()
      |> DateTime.add(-lookback_seconds, :second)
      |> DateTime.truncate(:second)

    _ = fetch_and_process(since, state)
    {:noreply, state}
  end

  defp via_tuple(account_id),
    do: {:via, Registry, {DataIngestionService.Registry, {:cloudtrail, account_id}}}

  defp fetch_and_process(%DateTime{} = since, %{account: account} = state) do
    aws_config = build_aws_config(account)

    start_time = since |> DateTime.truncate(:second)
    end_time = DateTime.utc_now() |> DateTime.truncate(:second)

    op =
      OpJSON.new(:cloudtrail,
        data: %{
          "StartTime" => start_time,
          "EndTime" => end_time
        },
        headers: [
          {"X-Amz-Target", "com.amazonaws.cloudtrail.v20131101.CloudTrail_20131101.LookupEvents"},
          {"Content-Type", "application/x-amz-json-1.1"}
        ]
      )

    case ExAws.request(op, aws_config) do
      {:ok, %{"Events" => events}} when is_list(events) ->
        generic_events =
          events
          |> Enum.map(&to_generic_event(&1, state))
          |> Enum.reject(&is_nil/1)

        case generic_events do
          [] ->
            {:ok, nil}

          list ->
            _ = KafkaProducer.publish_events(list)

            newest =
              list
              |> Enum.map(& &1.event_time)
              |> Enum.reject(&is_nil/1)
              |> Enum.max_by(&DateTime.to_unix/1, fn -> nil end)

            {:ok, newest}
        end

      {:ok, _body} ->
        {:ok, nil}

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp build_aws_config(%CloudAccount{credentials: creds}) when is_map(creds) do
    akid =
      Map.get(creds, :access_key_id) ||
        Map.get(creds, "access_key_id") ||
        Map.get(creds, :aws_access_key_id) ||
        Map.get(creds, "aws_access_key_id")

    sak =
      Map.get(creds, :secret_access_key) ||
        Map.get(creds, "secret_access_key") ||
        Map.get(creds, :aws_secret_access_key) ||
        Map.get(creds, "aws_secret_access_key")

    region =
      Map.get(creds, :region) ||
        Map.get(creds, "region") ||
        Map.get(creds, :aws_region) ||
        Map.get(creds, "aws_region")

    session_token =
      Map.get(creds, :session_token) ||
        Map.get(creds, "session_token") ||
        Map.get(creds, :aws_session_token) ||
        Map.get(creds, "aws_session_token")

    config =
      [
        access_key_id: akid,
        secret_access_key: sak,
        region: region
      ]
      |> maybe_put(:security_token, session_token)

    config
  end

  defp to_generic_event(%{} = event, %{account: %CloudAccount{} = account}) do
    actor = Map.get(event, "Username")
    action = Map.get(event, "EventName")
    source = Map.get(event, "EventSource")
    event_time = parse_event_time(Map.get(event, "EventTime"))
    org_id = account.organization_id

    %GenericAuditEvent{
      organization_id: org_id,
      cloud_account_id: account.id,
      actor_identity: actor,
      action: action,
      event_time: event_time,
      source: source,
      raw: event
    }
  end

  defp to_generic_event(_, _), do: nil

  defp maybe_put(list, _key, nil), do: list
  defp maybe_put(list, key, value), do: Keyword.put(list, key, value)

  defp parse_event_time(nil), do: nil
  defp parse_event_time(%DateTime{} = dt), do: dt
  defp parse_event_time(float) when is_float(float), do: float |> trunc() |> parse_event_time()

  defp parse_event_time(int) when is_integer(int) do
    {unit, value} =
      cond do
        int >= 1_000_000_000_000 -> {:millisecond, int}
        int >= 1_000_000_000 -> {:second, int}
        true -> {:second, int}
      end

    case DateTime.from_unix(value, unit) do
      {:ok, dt} -> dt
      _ -> nil
    end
  end

  defp parse_event_time(str) when is_binary(str) do
    cond do
      String.match?(str, ~r/^\d+$/) ->
        str |> String.to_integer() |> parse_event_time()

      true ->
        case DateTime.from_iso8601(str) do
          {:ok, dt, _offset} -> dt
          _ -> nil
        end
    end
  end
end
