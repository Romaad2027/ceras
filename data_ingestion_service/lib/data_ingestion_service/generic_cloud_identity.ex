defmodule DataIngestionService.GenericCloudIdentity do
  @moduledoc """
  Generic cloud identity representation.
  """

  @derive Jason.Encoder
  @type t :: %__MODULE__{
          arn: String.t() | nil,
          name: String.t() | nil,
          type: :iam_user,
          created_at: DateTime.t() | nil
        }

  defstruct [
    :arn,
    :name,
    :type,
    :created_at
  ]
end
