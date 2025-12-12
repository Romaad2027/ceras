# lib/data_ingestion_service/api_client.ex

defmodule DataIngestionService.ApiClient do
  @analysis_service_url "http://127.0.0.1:8000/api/v1/analyze/resource"

  def send_for_analysis(resources) do
    # Обробляємо кожен ресурс окремо
    Enum.each(resources, fn resource ->
      IO.puts("  -- Відправка '#{resource.resource_id}'")

      IO.inspect(resource)

      # Створюємо запит
      request =
        Finch.build(:post, @analysis_service_url, [], Jason.encode!(resource, enums: :string))

      # Відправляємо його
      case Finch.request(request, MyFinch) do
        {:ok, %{status: 200, body: body}} ->
          handle_success(body)

        {:ok, response} ->
          IO.puts("❌ Помилка від сервісу аналізу: Статус #{response.status}")

        {:error, reason} ->
          IO.puts("❌ Неможливо підключитися до сервісу аналізу: #{inspect(reason)}")
      end
    end)
  end

  defp handle_success(body) do
    case Jason.decode!(body) do
      [] ->
        IO.puts("✅ Ризиків не знайдено.")

      risks ->
        IO.puts("🚨 Знайдено ризики:")

        Enum.each(risks, fn risk ->
          IO.puts("   - [#{risk["severity"]}] #{risk["description"]}")
        end)
    end
  end
end
