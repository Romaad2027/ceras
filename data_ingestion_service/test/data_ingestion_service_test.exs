defmodule DataIngestionServiceTest do
  use ExUnit.Case
  doctest DataIngestionService

  test "greets the world" do
    assert DataIngestionService.hello() == :world
  end
end
