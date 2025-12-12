defmodule DataIngestionService.DataCollectorsCtx.AwsProvider do
  @moduledoc false

  alias DataIngestionService.CloudResource
  alias DataIngestionService.APIClient.Aws
  alias DataIngestionService.DataCollectorsCtx.Transformers.AwsS3Normalizer
  import SweetXml

  @spec fetch_all_buckets_metadata() :: {:ok, [CloudResource.t()]} | {:error, term()}
  def fetch_all_buckets_metadata() do
    case fetch_all_buckets() do
      {:ok, buckets} ->
        resources =
          Enum.map(buckets, fn %{name: bucket_name} = bkt ->
            region = bucket_region(bucket_name)

            policy_json = fetch_policy_json(bucket_name, region)
            policy_status = fetch_policy_status_json(bucket_name, region)
            encryption = fetch_encryption_xml(bucket_name, region)
            versioning = fetch_versioning_xml(bucket_name, region)

            normalized_config =
              AwsS3Normalizer.build(%{
                policy_status: policy_status,
                policy_json: policy_json,
                encryption: encryption,
                versioning: versioning
              })

            %CloudResource{
              resource_id: bucket_name,
              resource_type: :storage_bucket,
              cloud_provider: :aws,
              account_id: System.get_env("AWS_ACCOUNT_ID") || "unknown",
              configuration:
                Map.merge(
                  %{
                    "bucket_name" => bucket_name,
                    "creation_date" => Map.get(bkt, :creation_date),
                    "region" => region
                  },
                  normalized_config
                )
            }
          end)

        {:ok, resources}

      {:error, reason} ->
        {:error, reason}
    end
  end

  @spec fetch_all_buckets() :: {:ok, list(map())} | {:error, term()}
  def fetch_all_buckets() do
    case Aws.list_buckets("eu-north-1") do
      {:ok, json, _xml} ->
        buckets = extract_buckets(json)
        {:ok, buckets}

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp bucket_region(bucket) do
    case Aws.get_bucket_location(bucket) do
      {:ok, %{"LocationConstraint" => region}} ->
        if region in [nil, ""], do: "eu-north-1", else: region

      {:ok, %{LocationConstraint: region}} ->
        if region in [nil, ""], do: "eu-north-1", else: region

      {:ok, %{body: xml}} ->
        s = to_string(xml)

        case Regex.run(~r/<LocationConstraint>(.*?)<\/LocationConstraint>/, s,
               capture: :all_but_first
             ) do
          ["" | _] -> "eu-north-1"
          [region | _] -> region
          _ -> "eu-north-1"
        end

      _ ->
        "eu-north-1"
    end
  end

  defp fetch_acl_json(bucket, region) do
    case Aws.get_bucket_acl(bucket, region) do
      {:ok, json, _xml} ->
        json

      _ ->
        nil
    end
  end

  defp fetch_policy_json(bucket, region) do
    case Aws.get_bucket_policy(bucket, region) do
      {:ok, %{body: json}} when is_binary(json) ->
        Jason.decode(json)
        |> case do
          {:ok, decoded} -> decoded
          _ -> nil
        end

      {:error, {:http_error, 404, _}} ->
        nil

      {:error, _} ->
        nil

      _ ->
        nil
    end
  end

  defp fetch_policy_status_json(bucket, region) do
    case Aws.get_bucket_policy_status(bucket, region) do
      {:ok, %{} = map} when is_map(map) ->
        if Map.has_key?(map, :body) do
          body_string = to_string(map.body)

          case Jason.decode(body_string) do
            {:ok, decoded} -> decoded
            _ -> xpath(body_string, ~x"//PolicyStatus", is_public: ~x"./IsPublic/text()"s)
          end
        else
          map
        end

      {:ok, %{body: body}} ->
        body_string = to_string(body)

        case Jason.decode(body_string) do
          {:ok, decoded} -> decoded
          _ -> xpath(body_string, ~x"//PolicyStatus", is_public: ~x"./IsPublic/text()"s)
        end

      _ ->
        nil
    end
  end

  defp fetch_public_access_block_xml(bucket, region) do
    case Aws.get_public_access_block(bucket, region) do
      {:ok, %{} = map} when is_map(map) ->
        if Map.has_key?(map, :body) do
          xml_string = to_string(map.body)

          xpath(xml_string, ~x"//PublicAccessBlockConfiguration",
            block_public_acls: ~x"./BlockPublicAcls/text()"s,
            ignore_public_acls: ~x"./IgnorePublicAcls/text()"s,
            block_public_policy: ~x"./BlockPublicPolicy/text()"s,
            restrict_public_buckets: ~x"./RestrictPublicBuckets/text()"s
          )
        else
          map
        end

      {:ok, %{body: xml}} ->
        xml_string = to_string(xml)

        xpath(xml_string, ~x"//PublicAccessBlockConfiguration",
          block_public_acls: ~x"./BlockPublicAcls/text()"s,
          ignore_public_acls: ~x"./IgnorePublicAcls/text()"s,
          block_public_policy: ~x"./BlockPublicPolicy/text()"s,
          restrict_public_buckets: ~x"./RestrictPublicBuckets/text()"s
        )

      _ ->
        nil
    end
  end

  defp fetch_encryption_xml(bucket, region) do
    case Aws.get_bucket_encryption(bucket, region) do
      {:ok, json, _xml} ->
        json

      _ ->
        nil
    end
  end

  defp fetch_versioning_xml(bucket, region) do
    case Aws.get_bucket_versioning(bucket, region) do
      {:ok, json, _xml} -> json
      _ -> nil
    end
  end

  defp extract_buckets(resp) do
    # Normalize various shapes from the aws library into
    # a list of %{name: String.t(), creation_date: String.t() | nil}
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
end
