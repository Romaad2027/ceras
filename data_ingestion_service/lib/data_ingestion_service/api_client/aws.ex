defmodule DataIngestionService.APIClient.Aws do
  @moduledoc false

  # Build AWS client using env credentials and provided or env/default region
  def aws_client(region) do
    config = Application.fetch_env!(:data_ingestion_service, __MODULE__)

    selected_region = config[:region]

    cond do
      is_binary(config[:access_key_id]) and is_binary(config[:secret_access_key]) ->
        AWS.Client.create(config[:access_key_id], config[:secret_access_key], selected_region)

      true ->
        nil
    end
  end

  # Buckets
  def list_buckets(region \\ nil) do
    case aws_client(region) do
      nil -> {:error, :missing_aws_credentials}
      client -> AWS.S3.list_buckets(client)
    end
  end

  def get_bucket_location(bucket, region \\ nil) do
    case aws_client(region) do
      nil -> {:error, :missing_aws_credentials}
      client -> AWS.S3.get_bucket_location(client, bucket)
    end
  end

  def get_bucket_acl(bucket, region \\ nil) do
    case aws_client(region) do
      nil -> {:error, :missing_aws_credentials}
      client -> AWS.S3.get_bucket_acl(client, bucket)
    end
  end

  # Objects
  def list_objects_v2(bucket, opts \\ [], region \\ nil) do
    case aws_client(region) do
      nil -> {:error, :missing_aws_credentials}
      client -> AWS.S3.list_objects_v2(client, bucket, opts)
    end
  end

  def get_object_acl(bucket, key, region \\ nil) do
    case aws_client(region) do
      nil -> {:error, :missing_aws_credentials}
      client -> AWS.S3.get_object_acl(client, bucket, key)
    end
  end

  def get_bucket_policy(bucket, region \\ nil) do
    ExAws.S3.get_bucket_policy(bucket)
    |> ExAws.request(region: region || System.get_env("AWS_REGION") || "eu-north-1")
  end

  def get_bucket_policy_status(bucket, region \\ nil) do
    %ExAws.Operation.S3{
      http_method: :get,
      bucket: bucket,
      path: "/",
      resource: "policyStatus"
    }
    |> ExAws.request(region: region || System.get_env("AWS_REGION") || "eu-north-1")
  end

  def get_public_access_block(bucket, region \\ nil) do
    case aws_client(region) do
      nil -> {:error, :missing_aws_credentials}
      client -> AWS.S3.get_public_access_block(client, bucket)
    end
  end

  def get_bucket_encryption(bucket, region \\ nil) do
    case aws_client(region) do
      nil -> {:error, :missing_aws_credentials}
      client -> AWS.S3.get_bucket_encryption(client, bucket)
    end
  end

  def get_bucket_versioning(bucket, region \\ nil) do
    case aws_client(region) do
      nil -> {:error, :missing_aws_credentials}
      client -> AWS.S3.get_bucket_versioning(client, bucket)
    end
  end
end
