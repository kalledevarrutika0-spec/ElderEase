from fastapi import APIRouter

from app.api.routers.assistant import router as assistant_router
from app.api.routers.appointments import router as appointments_router
from app.api.routers.caregivers import router as caregivers_router
from app.api.routers.dashboard import router as dashboard_router
from app.api.routers.doses import router as doses_router
from app.api.routers.health import router as health_router
from app.api.routers.medicines import router as medicines_router
from app.api.routers.notifications import router as notifications_router
from app.api.routers.stock import router as stock_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(assistant_router)
api_router.include_router(dashboard_router)
api_router.include_router(medicines_router)
api_router.include_router(stock_router)
api_router.include_router(doses_router)
api_router.include_router(appointments_router)
api_router.include_router(caregivers_router)
api_router.include_router(notifications_router)
