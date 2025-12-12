defmodule DataIngestionService.Workers.CloudAccountWatcher do
  @moduledoc """
  Periodically ensures a provider poller is running per active cloud account.
  """

  use GenServer
  require Logger

  alias DataIngestionService.Repo
  alias DataIngestionService.Workers.CloudtrailPoller
  alias DataIngestionService.Schema.CloudAccount

  @default_interval_ms 60_000

  @type state :: %{
          interval_ms: non_neg_integer()
        }

  @spec start_link(keyword()) :: GenServer.on_start()
  def start_link(opts \\ []) do
    GenServer.start_link(__MODULE__, opts, name: __MODULE__)
  end

  @impl true
  def init(opts) do
    interval_ms = Keyword.get(opts, :interval_ms, @default_interval_ms)
    state = %{interval_ms: interval_ms}
    Process.send_after(self(), :tick, 0)
    {:ok, state}
  end

  @impl true
  def handle_info(:tick, %{interval_ms: interval_ms} = state) do
    ensure_pollers_started()
    Process.send_after(self(), :tick, interval_ms)
    {:noreply, state}
  end

  defp ensure_pollers_started do
    accounts = list_active_accounts()

    Enum.each(accounts, fn account ->
      case normalize_provider(account.provider) do
        "AWS" ->
          ensure_aws_cloudtrail_poller(account)

        "AZURE" ->
          # Placeholder for future Azure poller
          :ok

        _other ->
          :ok
      end
    end)
  end

  defp ensure_aws_cloudtrail_poller(%CloudAccount{} = account) do
    case Registry.lookup(DataIngestionService.Registry, {:cloudtrail, account.id}) do
      [] ->
        spec = {CloudtrailPoller, account}

        case DynamicSupervisor.start_child(DataIngestionService.PollerSupervisor, spec) do
          {:ok, _pid} ->
            org_id = account.organization_id
            Logger.info("Started CloudTrail poller for CloudAccount=#{account.id} org=#{org_id}")

          {:error, {:already_started, _pid}} ->
            :ok

          {:error, reason} ->
            Logger.error(
              "Failed to start CloudTrail poller for CloudAccount=#{account.id} reason=#{inspect(reason)}"
            )
        end

      _ ->
        :ok
    end
  end

  defp list_active_accounts do
    import Ecto.Query

    CloudAccount
    |> where([a], a.is_active == true)
    |> preload([:organization])
    |> Repo.all()
  end

  defp normalize_provider(nil), do: ""
  defp normalize_provider(p) when is_binary(p), do: String.upcase(p)
  defp normalize_provider(p), do: p |> to_string() |> String.upcase()
end
