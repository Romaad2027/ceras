# lib/data_ingestion_service/api_client.ex

defmodule DataIngestionService.ApiClient do
  require Logger
  @analysis_service_url "http://127.0.0.1:8000/api/v1/analyze/resource"

  def send_for_analysis(resources) do
    Enum.each(resources, fn resource ->
      IO.inspect(resource, label: "resource3232")

      request =
        Finch.build(:post, @analysis_service_url, [], Jason.encode!(resource))

      case Finch.request(request, MyFinch) |> IO.inspect(label: "request3232") do
        {:ok, %{status: 200, body: body}} ->
          IO.inspect(body, label: "body3232")
          handle_success(body)

        {:ok, %{status: 500, body: body}} ->
          Logger.error("Error sending for analysis: #{inspect(body)}")

        {:error, reason} ->
          IO.puts("Error sending for analysis: #{inspect(reason)}")
      end
    end)
  end

  defp handle_success(body) do
    case Jason.decode!(body) do
      [] ->
        IO.puts("No risks found.")

      risks ->
        IO.puts("Risks found:")

        Enum.each(risks, fn risk ->
          IO.puts("   - [#{risk["severity"]}] #{risk["description"]}")
        end)
    end
  end
end
