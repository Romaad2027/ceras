defmodule DataIngestionService.GenericCloudIdentity do
  @moduledoc """
  Generic cloud identity representation.
  """

  @derive Jason.Encoder
  @type t :: %__MODULE__{
          identity_arn: String.t() | nil,
          name: String.t() | nil,
          type: :iam_user,
          created_at: DateTime.t() | nil,
          organization_id: String.t() | nil
        }

  defstruct [
    :identity_arn,
    :name,
    :type,
    :created_at,
    :organization_id
  ]
end
