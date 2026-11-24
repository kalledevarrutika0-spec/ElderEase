from typing import Any

from mcp.server.fastmcp import FastMCP
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.refill_engine import get_refill_forecast, list_refill_forecasts


def _check_refill_status(
    session: Session,
    medicine_id: int | None = None,
) -> dict[str, Any]:
    if medicine_id is not None:
        forecast = get_refill_forecast(session, medicine_id)
        return {
            "total": 1,
            "forecasts": [forecast.model_dump(mode="json")],
        }

    forecasts, total = list_refill_forecasts(session, offset=0, limit=500)
    while len(forecasts) < total:
        page, _ = list_refill_forecasts(
            session, offset=len(forecasts), limit=500
        )
        if not page:
            break
        forecasts.extend(page)

    return {
        "total": total,
        "forecasts": [
            forecast.model_dump(mode="json") for forecast in forecasts
        ],
    }


def register_refill_tools(server: FastMCP) -> None:
    @server.tool()
    def check_refill_status(medicine_id: int | None = None) -> dict[str, Any]:
        """Return the existing refill forecast for one medicine or all medicines."""
        with SessionLocal() as session:
            return _check_refill_status(session, medicine_id)
