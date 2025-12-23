defmodule DataIngestionService.Providers.IamProvider do
  @moduledoc """
  Fetches IAM identities from AWS.
  """

  alias DataIngestionService.GenericCloudIdentity
  alias ExAws.Iam, as: ExAwsIam

  # @doc """
  # Fetch identities using default ExAws configuration.
  # """
  # @spec fetch_identities() :: {:ok, [GenericCloudIdentity.t()]} | {:error, term()}
  # def fetch_identities do
  #   fetch_identities([])
  # end

  @doc """
  Fetch identities using the provided ExAws configuration.
  """
  @spec fetch_identities(keyword(), String.t() | nil) ::
          {:ok, [GenericCloudIdentity.t()]} | {:error, term()}
  def fetch_identities(aws_config, organization_id \\ nil) when is_list(aws_config) do
    aws_config = ensure_region(aws_config)

    case ExAwsIam.list_users() |> ExAws.request(aws_config) do
      {:ok, response} ->
        users = extract_users_from_response(response)
        {:ok, Enum.map(users, &to_identity(&1, organization_id))}

      {:error, reason} ->
        {:error, reason}
    end
  end

  @spec to_identity(map(), String.t() | nil) :: GenericCloudIdentity.t()
  defp to_identity(user_map, organization_id) do
    %GenericCloudIdentity{
      identity_arn: fetch_user_value(user_map, ["Arn", :arn]),
      name: fetch_user_value(user_map, ["UserName", :user_name]),
      type: :iam_user,
      created_at: parse_time(fetch_user_value(user_map, ["CreateDate", :create_date])),
      organization_id: organization_id
    }
  end

  defp extract_users_from_response(%{"Users" => users}) when is_list(users), do: users

  defp extract_users_from_response(%{body: %{"ListUsersResult" => %{"Users" => users}}})
       when is_list(users),
       do: users

  defp extract_users_from_response(%{body: %{list_users_result: %{users: users}}})
       when is_list(users),
       do: users

  defp extract_users_from_response(%{body: %{"list_users_result" => %{"users" => users}}})
       when is_list(users),
       do: users

  defp extract_users_from_response(_), do: []

  defp fetch_user_value(map, keys) do
    Enum.find_value(keys, &Map.get(map, &1))
  end

  defp ensure_region(config) do
    Keyword.put(config, :region, "us-east-1")
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
