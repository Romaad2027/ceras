defmodule DataIngestionService.CloudResource do
  @derive Jason.Encoder
  @type t :: %__MODULE__{
          resource_id: String.t(),
          resource_type: atom(),
          cloud_provider: atom(),
          account_id: String.t(),
          configuration: map()
        }

  defstruct [
    :resource_id,
    :resource_type,
    :cloud_provider,
    :account_id,
    :configuration
  ]
end
