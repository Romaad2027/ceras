defmodule DataIngestionService.Schema.Organization do
  @moduledoc """
  Read-only Organization entity mapped to the `organizations` table.
  """

  use Ecto.Schema

  @primary_key {:id, :binary_id, autogenerate: false}
  @foreign_key_type :binary_id

  @type t :: %__MODULE__{
          id: Ecto.UUID.t(),
          name: String.t() | nil
        }

  schema "organizations" do
    field(:name, :string)
  end
end
