defmodule DataIngestionService.Providers.IamProvider do
  @moduledoc """
  Fetches IAM identities from AWS.
  """

  alias DataIngestionService.GenericCloudIdentity

  @doc """
  Fetch identities using default ExAws configuration.
  """
  @spec fetch_identities() :: {:ok, [GenericCloudIdentity.t()]} | {:error, term()}
  def fetch_identities do
    fetch_identities([])
  end

  @doc """
  Fetch identities using the provided ExAws configuration.
  """
  @spec fetch_identities(keyword()) :: {:ok, [GenericCloudIdentity.t()]} | {:error, term()}
  def fetch_identities(aws_config) when is_list(aws_config) do
    case ExAws.IAM.list_users() |> ExAws.request(aws_config) do
      {:ok, %{"Users" => users}} when is_list(users) ->
        {:ok, Enum.map(users, &to_identity/1)}

      {:ok, _} ->
        {:ok, []}

      {:error, reason} ->
        {:error, reason}
    end
  end

  @spec to_identity(map()) :: GenericCloudIdentity.t()
  defp to_identity(user_map) do
    %GenericCloudIdentity{
      arn: Map.get(user_map, "Arn"),
      name: Map.get(user_map, "UserName"),
      type: :iam_user,
      created_at: parse_time(Map.get(user_map, "CreateDate"))
    }
  end

  defp parse_time(nil), do: nil
  defp parse_time(%DateTime{} = dt), do: dt

  defp parse_time(str) when is_binary(str) do
    case DateTime.from_iso8601(str) do
      {:ok, dt, _} -> dt
      _ -> nil
    end
  end
end
