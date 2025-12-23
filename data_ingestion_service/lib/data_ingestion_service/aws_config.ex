defmodule DataIngestionService.AwsConfig do
  @moduledoc """
  Helpers for building AWS credential configs that can drive the shared API client.
  """

  require Macro

  alias DataIngestionService.Schema.CloudAccount

  @spec build_for_account(CloudAccount.t()) :: keyword()
  def build_for_account(%CloudAccount{} = account) do
    build_from_credentials(account.credentials || %{}, account.region)
  end

  @spec build_from_credentials(map(), String.t() | nil) :: keyword()
  def build_from_credentials(creds, region \\ nil) when is_map(creds) do
    final_region =
      region ||
        credential_value(creds, :region) ||
        credential_value(creds, :aws_region)

    [
      access_key_id: credential_value(creds, :access_key_id),
      secret_access_key: credential_value(creds, :secret_access_key),
      session_token: credential_value(creds, :session_token),
      region: final_region
    ]
    |> Enum.reject(fn {_key, value} -> is_nil(value) end)
  end

  @spec has_access_key_fields?(map() | nil) :: boolean()
  def has_access_key_fields?(creds) when is_map(creds) do
    has_key_field?(creds, "accessKeyId") && has_key_field?(creds, "secretAccessKey")
  end

  def has_access_key_fields?(_), do: false

  defp has_key_field?(map, key) do
    Map.has_key?(map, key) || Map.has_key?(map, String.to_atom(key))
  end

  defp credential_value(creds, base) when is_atom(base) do
    credential_keys(base)
    |> Enum.find_value(fn key -> Map.get(creds, key) end)
  end

  defp credential_keys(base) when is_atom(base) do
    base_string = Atom.to_string(base)
    camel = base_string |> Macro.camelize() |> decapitalize()

    [
      base,
      String.to_atom(base_string),
      String.to_atom("aws_#{base_string}"),
      "aws_#{base_string}",
      base_string,
      camel
    ]
    |> Enum.uniq()
  end

  defp decapitalize(<<first::utf8, rest::binary>>) do
    <<String.downcase(<<first::utf8>>)::binary, rest::binary>>
  end

  defp decapitalize(other), do: other
end
