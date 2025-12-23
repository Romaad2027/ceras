defmodule DataIngestionService.Workers.CloudtrailCron do
  @moduledoc """
  Oban worker that triggers CloudTrail polling across all active cloud accounts.

  It sends a `poll_now/2` cast to each running `CloudtrailPoller` process, with an optional
  `lookback_seconds` argument provided via job args (default: 600s).
  """

  use Oban.Worker,
    queue: :cloudtrail,
    max_attempts: 1,
    unique: [period: 55]

  alias DataIngestionService.Repo
  alias DataIngestionService.Schema.CloudAccount
  alias DataIngestionService.Workers.CloudtrailPoller

  @impl Oban.Worker
  @spec perform(%Oban.Job{}) :: :ok
  def perform(%Oban.Job{args: args}) when is_map(args) do
    lookback_seconds =
      Map.get(args, "lookback_seconds") ||
        Map.get(args, :lookback_seconds) ||
        600

    active_accounts()
    |> Enum.each(fn %CloudAccount{id: account_id} = account ->
      case Registry.lookup(DataIngestionService.Registry, {:cloudtrail, account_id}) do
        [{pid, _meta}] when is_pid(pid) ->
          :ok = CloudtrailPoller.poll_now(pid, normalize_lookback(lookback_seconds))

        _ ->
          # Best-effort start if missing; watcher should handle it normally.
          _ = start_poller_if_needed(account)

          case Registry.lookup(DataIngestionService.Registry, {:cloudtrail, account_id}) do
            [{pid, _}] when is_pid(pid) ->
              :ok = CloudtrailPoller.poll_now(pid, normalize_lookback(lookback_seconds))

            _ ->
              :ok
          end
      end
    end)

    :ok
  end

  defp normalize_lookback(val) when is_integer(val) and val > 0, do: val

  defp normalize_lookback(val) when is_binary(val) do
    case Integer.parse(val) do
      {int, _} when int > 0 -> int
      _ -> 600
    end
  end

  defp normalize_lookback(_), do: 600

  defp active_accounts do
    import Ecto.Query

    CloudAccount
    |> where([a], a.is_active == true)
    |> preload([:organization])
    |> Repo.all()
  end

  defp start_poller_if_needed(%CloudAccount{} = account) do
    spec = {CloudtrailPoller, account}
    _ = DynamicSupervisor.start_child(DataIngestionService.PollerSupervisor, spec)
    :ok
  end
end
