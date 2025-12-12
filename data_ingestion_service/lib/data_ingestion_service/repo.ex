defmodule DataIngestionService.Repo do
  use Ecto.Repo,
    otp_app: :data_ingestion_service,
    adapter: Ecto.Adapters.Postgres
end
