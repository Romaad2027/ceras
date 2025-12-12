defmodule DataIngestionService.DataCollectorsCtx.Transformers.AwsS3Normalizer do
  @moduledoc false

  @spec build(%{
          optional(:policy_status) => any(),
          optional(:policy_json) => any(),
          optional(:encryption) => any(),
          optional(:versioning) => any()
        }) :: map()
  def build(%{
        policy_status: policy_status,
        policy_json: policy_json,
        encryption: encryption,
        versioning: versioning
      }) do
    %{
      "is_public" => derive_is_public(policy_status, policy_json),
      "encryption_type" => derive_encryption_type(encryption),
      "versioning_enabled" => derive_versioning_enabled(versioning),
      "access_logging_enabled" => false
    }
  end

  def build(%{} = opts) do
    build(%{
      policy_status: Map.get(opts, :policy_status),
      policy_json: Map.get(opts, :policy_json),
      encryption: Map.get(opts, :encryption),
      versioning: Map.get(opts, :versioning)
    })
  end

  # is_public
  defp derive_is_public(policy_status, policy_json) do
    from_status =
      cond do
        is_map(policy_status) and Map.has_key?(policy_status, "PolicyStatus") ->
          policy_status
          |> Map.get("PolicyStatus")
          |> get_truthy(["IsPublic", :IsPublic])

        is_map(policy_status) and Map.has_key?(policy_status, :PolicyStatus) ->
          policy_status
          |> Map.get(:PolicyStatus)
          |> get_truthy(["IsPublic", :IsPublic])

        is_map(policy_status) and Map.has_key?(policy_status, :is_public) ->
          policy_status |> Map.get(:is_public) |> as_bool()

        true ->
          false
      end

    from_policy =
      cond do
        is_map(policy_json) ->
          statements =
            Map.get(policy_json, "Statement") ||
              Map.get(policy_json, :Statement)

          normalize_statements(statements)
          |> Enum.any?(fn stmt ->
            effect = Map.get(stmt, "Effect") || Map.get(stmt, :Effect)
            principal = Map.get(stmt, "Principal") || Map.get(stmt, :Principal)
            allow? = is_binary(effect) and String.upcase(effect) == "ALLOW"

            public_principal? =
              principal == "*" or
                (is_map(principal) and
                   (Map.get(principal, "AWS") == "*" or Map.get(principal, :AWS) == "*"))

            allow? and public_principal?
          end)

        true ->
          false
      end

    from_status or from_policy
  end

  defp normalize_statements(nil), do: []
  defp normalize_statements(list) when is_list(list), do: list
  defp normalize_statements(map) when is_map(map), do: [map]
  defp normalize_statements(_), do: []

  # encryption_type
  defp derive_encryption_type(nil), do: "NONE"

  defp derive_encryption_type(encryption) do
    found = deep_find(encryption, ["SSEAlgorithm", :SSEAlgorithm, :sse_algorithm])

    case found do
      nil -> "NONE"
      val when is_binary(val) -> val
      val -> to_string(val)
    end
  end

  # versioning_enabled
  defp derive_versioning_enabled(nil), do: false

  defp derive_versioning_enabled(versioning) do
    status =
      deep_find(versioning, ["Status", :Status, :status])
      |> case do
        nil -> ""
        val when is_binary(val) -> val
        val -> to_string(val)
      end

    String.downcase(status) == "enabled"
  end

  # helpers
  defp get_truthy(nil, _keys), do: false

  defp get_truthy(map, keys) when is_map(map) do
    keys
    |> Enum.find_value(fn k ->
      case Map.get(map, k) do
        nil -> nil
        v -> as_bool(v)
      end
    end) || false
  end

  defp as_bool(v) when is_boolean(v), do: v
  defp as_bool(v) when is_binary(v), do: String.downcase(v) == "true"
  defp as_bool(_), do: false

  defp deep_find(value, _keys) when not is_map(value), do: nil

  defp deep_find(map, keys) when is_map(map) do
    Enum.find_value(keys, fn k -> Map.get(map, k) end) ||
      map
      |> Enum.find_value(fn
        {_k, v} when is_map(v) -> deep_find(v, keys)
        {_k, v} when is_list(v) -> deep_find_list(v, keys)
        _ -> nil
      end)
  end

  defp deep_find_list(list, keys) do
    Enum.find_value(list, fn
      v when is_map(v) -> deep_find(v, keys)
      v when is_list(v) -> deep_find_list(v, keys)
      _ -> nil
    end)
  end
end
