from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.database import Base
from app.models import Caregiver, Medicine
from app.services import assistant_service


def _create_mcp_database(path: Path) -> str:
    database_url = f"sqlite:///{path.as_posix()}"
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
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


class FakeGeminiClient:
    def __init__(self, *, answer="The available supply covers the next seven days."):
        self.answer = answer
        self.contents = None
        self.model = None
        self.closed = False
        self.aio = SimpleNamespace(
            models=SimpleNamespace(generate_content=self.generate_content),
            aclose=self.aclose,
        )

    async def generate_content(self, *, model, contents, config):
        self.model = model
        self.contents = contents
        self.config = config
        return SimpleNamespace(text=self.answer)

    async def aclose(self):
        self.closed = True


def test_chat_discovers_and_invokes_real_refill_mcp_tool(api, monkeypatch, tmp_path):
    database_url = _create_mcp_database(tmp_path / "assistant-mcp.db")
    monkeypatch.setattr(assistant_service.settings, "database_url", database_url)
    monkeypatch.setattr(
        assistant_service.settings, "gemini_api_key", SecretStr("test-key-not-real")
    )
    fake_client = FakeGeminiClient()
    monkeypatch.setattr(assistant_service.genai, "Client", lambda **kwargs: fake_client)
    message = "Will Grandpa's medicines last for seven days?"

    response = api["client"].post("/api/assistant/chat", json={"message": message})

    assert response.status_code == 200
    result = response.json()
    assert result["message"] == fake_client.answer
    assert result["tool_name"] == "check_refill_status"
    assert result["tool_result"]["total"] == 1
    forecast = result["tool_result"]["forecasts"][0]
    assert forecast["medicine_name"] == "Seven Day Test Medicine"
    assert forecast["current_available_stock"] == "30.000"
    assert forecast["forecast_available"] is True
    assert fake_client.model == assistant_service.settings.gemini_model
    assert message in fake_client.contents
    assert "Seven Day Test Medicine" in fake_client.contents
    assert fake_client.closed is True
    assert "test-key-not-real" not in response.text


@pytest.mark.parametrize(
    "api_key",
    [None, SecretStr("replace_with_your_gemini_api_key")],
)
def test_chat_reports_missing_gemini_configuration(api, monkeypatch, api_key):
    monkeypatch.setattr(assistant_service.settings, "gemini_api_key", api_key)

    response = api["client"].post(
        "/api/assistant/chat",
        json={"message": "Will Grandpa's medicines last for seven days?"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "assistant_not_configured"
    assert "GEMINI_API_KEY" in response.json()["error"]["message"]


def test_gemini_settings_load_from_backend_env_file_without_exposing_secret(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GEMINI_API_KEY=temporary-test-key\nGEMINI_MODEL=gemini-test-model\n",
        encoding="utf-8",
    )

    configured = Settings(_env_file=env_file)

    assert configured.gemini_api_key is not None
    assert configured.gemini_api_key.get_secret_value() == "temporary-test-key"
    assert str(configured.gemini_api_key) == "**********"
    assert configured.gemini_model == "gemini-test-model"


def test_chat_reports_gemini_failure_without_fabricating_success(
    api, monkeypatch
):
    monkeypatch.setattr(
        assistant_service.settings, "gemini_api_key", SecretStr("test-key-not-real")
    )

    async def actual_forecast_result():
        return {
            "total": 0,
            "forecasts": [],
        }

    monkeypatch.setattr(
        assistant_service, "invoke_refill_status_tool", actual_forecast_result
    )
    fake_client = FakeGeminiClient()

    async def fail_generation(**kwargs):
        raise RuntimeError("provider unavailable")

    fake_client.aio.models.generate_content = fail_generation
    monkeypatch.setattr(assistant_service.genai, "Client", lambda **kwargs: fake_client)

    response = api["client"].post(
        "/api/assistant/chat",
        json={"message": "Will Grandpa's medicines last for seven days?"},
    )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "assistant_workflow_failed"
    assert "Gemini could not generate an answer" in response.json()["error"]["message"]
    assert "tool_result" not in response.json()
    assert fake_client.closed is True


def test_chat_reports_mcp_failure_without_fabricating_success(api, monkeypatch):
    monkeypatch.setattr(
        assistant_service.settings, "gemini_api_key", SecretStr("test-key-not-real")
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
