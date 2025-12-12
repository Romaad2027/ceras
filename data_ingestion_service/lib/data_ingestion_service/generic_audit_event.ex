defmodule DataIngestionService.GenericAuditEvent do
  @moduledoc """
  Generic audit event representation used for normalization across providers.
  """

  @derive Jason.Encoder
  @type t :: %__MODULE__{
          organization_id: String.t() | nil,
          cloud_account_id: String.t() | nil,
          actor_identity: String.t() | nil,
          action: String.t() | nil,
          event_time: DateTime.t() | nil,
          source: String.t() | nil,
          raw: map()
        }

  defstruct [
    :organization_id,
    :cloud_account_id,
    :actor_identity,
    :action,
    :event_time,
    :source,
    :raw
  ]
end
