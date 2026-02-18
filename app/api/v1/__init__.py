from app.api.v1 import clinical, health

api_router = APIRouter(prefix="/api/v1")

# Include all v1 routers
api_router.include_router(health.router)
api_router.include_router(clinical.router)
