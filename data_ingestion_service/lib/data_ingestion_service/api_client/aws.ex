defmodule DataIngestionService.APIClient.Aws do
  @moduledoc false

  # Build AWS client using env credentials or provided per-account config.
  def aws_client(region \\ nil, aws_config \\ []) do
    config = final_config(aws_config, region)

    cond do
      is_binary(config[:access_key_id]) and is_binary(config[:secret_access_key]) ->
        AWS.Client.create(config[:access_key_id], config[:secret_access_key], config[:region])

      true ->
        nil
    end
  end

  # Buckets
  def list_buckets(region \\ nil, aws_config \\ []) do
    case aws_client(region, aws_config) do
      nil -> {:error, :missing_aws_credentials}
      client -> AWS.S3.list_buckets(client)
    end
  end

  def get_bucket_location(bucket, region \\ nil, aws_config \\ []) do
    case aws_client(region, aws_config) do
      nil -> {:error, :missing_aws_credentials}
      client -> AWS.S3.get_bucket_location(client, bucket)
    end
  end

  def get_bucket_acl(bucket, region \\ nil, aws_config \\ []) do
    case aws_client(region, aws_config) do
      nil -> {:error, :missing_aws_credentials}
      client -> AWS.S3.get_bucket_acl(client, bucket)
    end
  end

  # Objects
  def list_objects_v2(bucket, opts \\ [], region \\ nil, aws_config \\ []) do
    case aws_client(region, aws_config) do
      nil -> {:error, :missing_aws_credentials}
      client -> AWS.S3.list_objects_v2(client, bucket, opts)
    end
  end

  def get_object_acl(bucket, key, region \\ nil, aws_config \\ []) do
    case aws_client(region, aws_config) do
      nil -> {:error, :missing_aws_credentials}
      client -> AWS.S3.get_object_acl(client, bucket, key)
    end
  end

  def get_bucket_policy(bucket, region \\ nil, aws_config \\ []) do
    config = final_config(aws_config, region)

    ExAws.S3.get_bucket_policy(bucket)
    |> ExAws.request(config)
  end

  def get_bucket_policy_status(bucket, region \\ nil, aws_config \\ []) do
    config = final_config(aws_config, region)

    %ExAws.Operation.S3{
      http_method: :get,
      bucket: bucket,
      path: "/",
      resource: "policyStatus"
    }
    |> ExAws.request(config)
  end

  def get_public_access_block(bucket, region \\ nil, aws_config \\ []) do
    case aws_client(region, aws_config) do
      nil -> {:error, :missing_aws_credentials}
      client -> AWS.S3.get_public_access_block(client, bucket)
    end
  end

  def get_bucket_encryption(bucket, region \\ nil, aws_config \\ []) do
    case aws_client(region, aws_config) do
      nil -> {:error, :missing_aws_credentials}
      client -> AWS.S3.get_bucket_encryption(client, bucket)
    end
  end

  def get_bucket_versioning(bucket, region \\ nil, aws_config \\ []) do
    case aws_client(region, aws_config) do
      nil -> {:error, :missing_aws_credentials}
      client -> AWS.S3.get_bucket_versioning(client, bucket)
    end
  end

  defp final_config(aws_config, region) do
    base_config = Application.get_env(:data_ingestion_service, __MODULE__, [])
    merged_config = base_config |> Keyword.merge(aws_config || [])
    selected_region = region || Keyword.get(merged_config, :region) || default_region()
    Keyword.put(merged_config, :region, selected_region)
  end

  defp default_region do
    Application.get_env(:data_ingestion_service, __MODULE__, [])
    |> Keyword.get(:region) || "eu-north-1"
  end
end
