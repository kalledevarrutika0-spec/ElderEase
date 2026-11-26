import json
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
import httpx
from openai import APIStatusError
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.database import Base
from app.models import Caregiver, Medicine
from app.services import assistant_service


def _create_mcp_database(path: Path, *, include_medicine: bool = True) -> str:
    database_url = f"sqlite:///{path.as_posix()}"
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    if include_medicine:
        with Session(engine) as session:
            caregiver = Caregiver(name="Test Caregiver", relationship="daughter")
            medicine = Medicine(
                name="Seven Day Test Medicine",
                dosage="1 tablet",
                units_per_dose=Decimal("1"),
                frequency_per_day=2,
                scheduled_times=["08:00", "20:00"],
                current_stock=Decimal("30"),
                refill_threshold=Decimal("5"),
                assigned_caregiver=caregiver,
            )
            session.add(medicine)
            session.commit()
    engine.dispose()
    return database_url


class FakeGroqClient:
    def __init__(self, *, api_key, answer="The available supply covers the next seven days."):
        self.api_key = api_key
        self.answer = answer
        self.input = None
        self.instructions = None
        self.model = None
        self.closed = False
        self.responses = SimpleNamespace(create=self.create_response)

    async def create_response(self, *, model, instructions, input, temperature):
        self.model = model
        self.instructions = instructions
        self.input = input
        self.temperature = temperature
        return SimpleNamespace(output_text=self.answer)

    async def close(self):
        self.closed = True


def test_chat_discovers_and_invokes_real_refill_mcp_tool(api, monkeypatch, tmp_path):
    database_url = _create_mcp_database(tmp_path / "assistant-mcp.db")
    monkeypatch.setattr(assistant_service.settings, "database_url", database_url)
    monkeypatch.setattr(
        assistant_service.settings, "groq_api_key", SecretStr("test-key-not-real")
    )
    groq_base_url = "https://api.groq.com/openai/v1"
    monkeypatch.setattr(assistant_service.settings, "groq_base_url", groq_base_url)
    monkeypatch.setattr(assistant_service.settings, "groq_model", "openai/test-model")
    answer = "I'm checking Elderease’s refill-status forecast."
    fake_client = FakeGroqClient(api_key="test-key-not-real", answer=answer)
    client_options = {}

    def create_client(**kwargs):
        client_options.update(kwargs)
        return fake_client

    monkeypatch.setattr(assistant_service, "AsyncOpenAI", create_client)
    message = "Will Grandpa's medicines last for seven days?"

    response = api["client"].post("/api/assistant/chat", json={"message": message})

    assert response.status_code == 200
    result = response.json()
    assert result["message"] == answer
    assert json.loads(response.content.decode("utf-8"))["message"] == answer
    assert response.headers["content-type"].startswith("application/json")
    assert result["tool_name"] == "check_refill_status"
    assert result["tool_result"]["total"] == 1
    forecast = result["tool_result"]["forecasts"][0]
    assert forecast["medicine_name"] == "Seven Day Test Medicine"
    assert forecast["current_available_stock"] == "30.000"
    assert forecast["forecast_available"] is True
    assert fake_client.model == "openai/test-model"
    assert fake_client.api_key == "test-key-not-real"
    assert client_options == {
        "api_key": "test-key-not-real",
        "base_url": groq_base_url,
    }
    assert message in fake_client.input
    assert "Seven Day Test Medicine" in fake_client.input
    assert "using only the supplied check_refill_status tool result" in fake_client.instructions
    assert "diagnose conditions" in fake_client.instructions
    assert "changing medication dosage" in fake_client.instructions
    assert fake_client.temperature == 0.2
    assert fake_client.closed is True
    assert "test-key-not-real" not in response.text


def test_chat_passes_empty_refill_tool_result_to_groq(api, monkeypatch, tmp_path):
    database_url = _create_mcp_database(
        tmp_path / "assistant-empty-mcp.db", include_medicine=False
    )
    monkeypatch.setattr(assistant_service.settings, "database_url", database_url)
    monkeypatch.setattr(
        assistant_service.settings, "groq_api_key", SecretStr("test-key-not-real")
    )
    fake_client = FakeGroqClient(
        api_key="test-key-not-real",
        answer="There are no refill forecasts in the supplied result.",
    )
    monkeypatch.setattr(
        assistant_service, "AsyncOpenAI", lambda **kwargs: fake_client
    )

    response = api["client"].post(
        "/api/assistant/chat",
        json={"message": "Will Grandpa's medicines last for seven days?"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["tool_result"] == {"total": 0, "forecasts": []}
    assert '"total": 0, "forecasts": []' in fake_client.input
    assert result["message"] == fake_client.answer
    assert fake_client.closed is True


@pytest.mark.parametrize(
    "api_key",
    [None, SecretStr("replace_with_your_groq_api_key")],
)
def test_chat_reports_missing_groq_configuration(api, monkeypatch, api_key):
    monkeypatch.setattr(assistant_service.settings, "groq_api_key", api_key)

    response = api["client"].post(
        "/api/assistant/chat",
        json={"message": "Will Grandpa's medicines last for seven days?"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "assistant_not_configured"
    assert "GROQ_API_KEY" in response.json()["error"]["message"]


def test_groq_settings_load_from_backend_env_file_without_exposing_secret(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GROQ_API_KEY=temporary-test-key\n"
        "GROQ_BASE_URL=https://api.groq.com/openai/v1\n"
        "GROQ_MODEL=openai/test-model\n",
        encoding="utf-8",
    )

    configured = Settings(_env_file=env_file)

    assert configured.groq_api_key is not None
    assert configured.groq_api_key.get_secret_value() == "temporary-test-key"
    assert str(configured.groq_api_key) == "**********"
    assert configured.groq_base_url == "https://api.groq.com/openai/v1"
    assert configured.groq_model == "openai/test-model"


def test_chat_reports_groq_failure_without_fabricating_success(
    api, monkeypatch, caplog
):
    monkeypatch.setattr(
        assistant_service.settings, "groq_api_key", SecretStr("test-key-not-real")
    )

    async def actual_forecast_result():
        return {
            "total": 0,
            "forecasts": [],
        }

    monkeypatch.setattr(
        assistant_service, "invoke_refill_status_tool", actual_forecast_result
    )
    fake_client = FakeGroqClient(api_key="test-key-not-real")

    async def fail_generation(**kwargs):
        raise RuntimeError("provider unavailable")

    fake_client.responses.create = fail_generation
    monkeypatch.setattr(
        assistant_service, "AsyncOpenAI", lambda **kwargs: fake_client
    )

    response = api["client"].post(
        "/api/assistant/chat",
        json={"message": "Will Grandpa's medicines last for seven days?"},
    )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "assistant_workflow_failed"
    assert "Groq could not generate an answer" in response.json()["error"]["message"]
    assert "tool_result" not in response.json()
    assert fake_client.closed is True
    assert "test-key-not-real" not in response.text
    assert "test-key-not-real" not in caplog.text


def test_groq_api_error_logs_sanitized_provider_details(
    api, monkeypatch, caplog
):
    api_key = "test-key-not-real"
    monkeypatch.setattr(
        assistant_service.settings, "groq_api_key", SecretStr(api_key)
    )

    async def actual_forecast_result():
        return {"total": 0, "forecasts": []}

    monkeypatch.setattr(
        assistant_service, "invoke_refill_status_tool", actual_forecast_result
    )
    request = httpx.Request(
        "POST",
        "https://api.groq.com/openai/v1/responses",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    provider_response = httpx.Response(401, request=request)
    provider_error = APIStatusError(
        f"Incorrect API key provided: {api_key}",
        response=provider_response,
        body={
            "error": {
                "message": f"Incorrect API key provided: {api_key}",
                "type": "authentication_error",
                "code": "invalid_api_key",
            }
        },
    )
    fake_client = FakeGroqClient(api_key=api_key)

    async def fail_generation(**kwargs):
        raise provider_error

    fake_client.responses.create = fail_generation
    monkeypatch.setattr(
        assistant_service, "AsyncOpenAI", lambda **kwargs: fake_client
    )

    response = api["client"].post(
        "/api/assistant/chat",
        json={"message": "Will Grandpa's medicines last for seven days?"},
    )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "assistant_workflow_failed"
    assert "http_status=401" in caplog.text
    assert "error_code=invalid_api_key" in caplog.text
    assert "error_type=authentication_error" in caplog.text
    assert "Incorrect API key provided: [REDACTED]" in caplog.text
    assert api_key not in caplog.text
    assert "Authorization" not in caplog.text
    assert "Bearer" not in caplog.text
    assert api_key not in response.text
    assert fake_client.closed is True


def test_chat_reports_mcp_failure_without_fabricating_success(api, monkeypatch):
    monkeypatch.setattr(
        assistant_service.settings, "groq_api_key", SecretStr("test-key-not-real")
    )

    async def fail_mcp_call():
        raise RuntimeError("MCP server unavailable")

    monkeypatch.setattr(assistant_service, "invoke_refill_status_tool", fail_mcp_call)

    response = api["client"].post(
        "/api/assistant/chat",
        json={"message": "Will Grandpa's medicines last for seven days?"},
    )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "assistant_workflow_failed"
    assert "MCP tool could not be reached" in response.json()["error"]["message"]
    assert "tool_result" not in response.json()


@pytest.mark.parametrize("message", ["", "   ", " " * 2001])
def test_chat_rejects_empty_or_oversized_messages(api, message):
    response = api["client"].post(
        "/api/assistant/chat",
        json={"message": message},
    )

    assert response.status_code == 422
