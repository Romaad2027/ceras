defmodule DataIngestionService.Schema.CloudAccount do
  @moduledoc """
  Read-only CloudAccount entity mapped to the `cloud_accounts` table.
  """

  use Ecto.Schema

  @primary_key {:id, :binary_id, autogenerate: false}
  @foreign_key_type :binary_id

  alias DataIngestionService.Schema.Organization

  @type provider :: String.t()

  @type t :: %__MODULE__{
          id: Ecto.UUID.t(),
          organization_id: Ecto.UUID.t(),
          provider: provider(),
          credentials: map(),
          is_active: boolean(),
          organization: Organization.t() | Ecto.Association.NotLoaded.t()
        }

  schema "cloud_accounts" do
    field(:provider, :string)
    field(:credentials, :map)
    field(:is_active, :boolean, default: false)
    field(:region, :string)
    belongs_to(:organization, Organization)
  end
end
