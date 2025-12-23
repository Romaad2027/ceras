defmodule DataIngestionService.DataCollectorsCtx.AwsProvider do
  @moduledoc false

  alias DataIngestionService.AwsConfig
  alias DataIngestionService.APIClient.Aws
  alias DataIngestionService.CloudResource
  alias DataIngestionService.DataCollectorsCtx.Transformers.AwsS3Normalizer
  alias DataIngestionService.Schema.CloudAccount

  import SweetXml

  @spec fetch_all_buckets_metadata(CloudAccount.t(), keyword()) ::
          {:ok, [CloudResource.t()]} | {:error, term()}
  def fetch_all_buckets_metadata(%CloudAccount{} = account, opts \\ []) do
    IO.inspect(account, label: "fetch_all_buckets_metadata3232")

    if credentials_available?(account) do
      aws_config = AwsConfig.build_for_account(account)

      region =
        Keyword.get(opts, :region) ||
          account.region ||
          default_region()

      case Aws.list_buckets(region, aws_config) do
        {:ok, response, _} ->
          build_resources(response, account, aws_config)

        {:error, reason} ->
          {:error, reason}
      end
    else
      IO.inspect(account, label: "missing_aws_credentials3232")
      {:error, :missing_aws_credentials}
    end
  end

  defp credentials_available?(%CloudAccount{credentials: creds}) do
    AwsConfig.has_access_key_fields?(creds)
  end

  defp credentials_available?(_), do: false

  defp build_resources(response, account, aws_config) do
    response
    |> unwrap_response_body()
    |> extract_buckets()
    |> Enum.map(&build_bucket_resource(&1, account, aws_config))
    |> then(&{:ok, &1})
  end

  defp build_bucket_resource(%{name: bucket_name} = bucket, account, aws_config) do
    bucket_region = bucket_region(bucket_name, aws_config)

    normalized_config =
      AwsS3Normalizer.build(%{
        policy_status: fetch_policy_status_json(bucket_name, bucket_region, aws_config),
        policy_json: fetch_policy_json(bucket_name, bucket_region, aws_config),
        encryption: fetch_encryption_json(bucket_name, bucket_region, aws_config),
        versioning: fetch_versioning_json(bucket_name, bucket_region, aws_config)
      })

    %CloudResource{
      resource_id: "arn:aws:s3:::#{bucket_name}",
      resource_type: :storage_bucket,
      cloud_provider: :aws,
      account_id: account.id,
      configuration:
        Map.merge(
          %{
            "bucket_name" => bucket_name,
            "creation_date" => Map.get(bucket, :creation_date),
            "region" => bucket_region
          },
          normalized_config
        )
    }
  end

  defp fetch_policy_json(bucket, region, aws_config) do
    case Aws.get_bucket_policy(bucket, region, aws_config) do
      {:ok, response} -> normalize_policy_json(response)
      {:error, {:http_error, 404, _}} -> nil
      _ -> nil
    end
  end

  defp fetch_policy_status_json(bucket, region, aws_config) do
    case Aws.get_bucket_policy_status(bucket, region, aws_config) do
      {:ok, response} -> normalize_policy_status(response)
      _ -> nil
    end
  end

  defp fetch_encryption_json(bucket, region, aws_config) do
    case Aws.get_bucket_encryption(bucket, region, aws_config) do
      {:ok, response, _} -> unwrap_response_body(response)
      _ -> nil
    end
  end

  defp fetch_versioning_json(bucket, region, aws_config) do
    case Aws.get_bucket_versioning(bucket, region, aws_config) do
      {:ok, response, _} -> unwrap_response_body(response)
      _ -> nil
    end
  end

  defp normalize_policy_json(response) do
    response
    |> unwrap_response_body()
    |> case do
      json when is_binary(json) -> decode_json(json)
      map when is_map(map) -> map
      _ -> nil
    end
  end

  defp normalize_policy_status(response) do
    response
    |> unwrap_response_body()
    |> case do
      map when is_map(map) -> map
      xml when is_binary(xml) -> decode_or_xpath_policy_status(xml)
      _ -> nil
    end
  end

  defp decode_or_xpath_policy_status(body_string) do
    case Jason.decode(body_string) do
      {:ok, decoded} -> decoded
      _ -> xpath(body_string, ~x"//PolicyStatus", is_public: ~x"./IsPublic/text()"s)
    end
  end

  defp decode_json(json) do
    case Jason.decode(json) do
      {:ok, decoded} -> decoded
      _ -> nil
    end
  end

  defp bucket_region(bucket, aws_config) do
    case Aws.get_bucket_location(bucket, nil, aws_config) do
      {:ok, response, _} ->
        response
        |> unwrap_response_body()
        |> parse_location_response()

      _ ->
        default_region()
    end
  end

  defp parse_location_response(%{"LocationConstraint" => region}), do: normalize_region(region)
  defp parse_location_response(%{LocationConstraint: region}), do: normalize_region(region)

  defp parse_location_response(region) when is_binary(region),
    do: region |> to_string() |> extract_region_from_xml()

  defp parse_location_response(_), do: default_region()

  defp extract_region_from_xml(xml_string) do
    case Regex.run(~r/<LocationConstraint>(.*?)<\/LocationConstraint>/, xml_string,
           capture: :all_but_first
         ) do
      [region] when region not in ["", nil] -> region
      _ -> default_region()
    end
  end

  defp normalize_region(nil), do: default_region()
  defp normalize_region(""), do: default_region()
  defp normalize_region(region), do: region

  defp extract_buckets(resp) do
    cond do
      is_map(resp) and Map.has_key?(resp, "ListAllMyBucketsResult") ->
        resp
        |> Map.get("ListAllMyBucketsResult")
        |> Map.get("Buckets", %{})
        |> extract_buckets_block()

      is_map(resp) and Map.has_key?(resp, "Buckets") ->
        resp
        |> Map.get("Buckets")
        |> extract_buckets_block()

      is_map(resp) and Map.has_key?(resp, :buckets) ->
        resp.buckets |> normalize_bucket_list()

      is_map(resp) and Map.has_key?(resp, :body) and is_map(resp.body) and
          Map.has_key?(resp.body, :buckets) ->
        resp.body.buckets |> normalize_bucket_list()

      true ->
        []
    end
  end

  defp extract_buckets_block(%{"Bucket" => list}) when is_list(list),
    do: normalize_bucket_list(list)

  defp extract_buckets_block(%{"Bucket" => bucket}) when is_map(bucket),
    do: normalize_bucket_list([bucket])

  defp extract_buckets_block(list) when is_list(list), do: normalize_bucket_list(list)
  defp extract_buckets_block(_), do: []

  defp normalize_bucket_list(list) do
    Enum.map(list, fn bucket ->
      name = Map.get(bucket, "Name") || Map.get(bucket, :name)
      creation_date = Map.get(bucket, "CreationDate") || Map.get(bucket, :creation_date)
      %{name: name, creation_date: creation_date}
    end)
  end

  defp unwrap_response_body(%{body: body}) when not is_nil(body), do: body
  defp unwrap_response_body(value), do: value

  defp default_region do
    Application.get_env(:data_ingestion_service, DataIngestionService.APIClient.Aws, [])
    |> Keyword.get(:region) || "eu-north-1"
  end
end
