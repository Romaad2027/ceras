defmodule DataIngestionService.MixProject do
  use Mix.Project

  def project do
    [
      app: :data_ingestion_service,
      version: "0.1.0",
      elixir: "~> 1.15",
      start_permanent: Mix.env() == :prod,
      deps: deps()
    ]
  end

  # Run "mix help compile.app" to learn about applications.
  def application do
    [
      extra_applications: [:logger],
      mod: {DataIngestionService.Application, []}
    ]
  end

  # Run "mix help deps" to learn about dependencies.
  defp deps do
    [
      {:finch, "~> 0.16"},
      {:jason, "~> 1.4"},
      {:ex_aws, "~> 2.4"},
      {:ex_aws_s3, "~> 2.4"},
      {:ex_aws_iam, "~> 4.0"},
      {:sweet_xml, "~> 0.7"},
      {:aws, "~> 1.0.0"},
      {:hackney, "~> 1.18"},
      {:brod, "~> 3.16"},
      {:ecto_sql, "~> 3.11"},
      {:postgrex, ">= 0.0.0"},
      {:oban, "~> 2.17"}
    ]
  end
end
