from app.api.routes.analysis import router as analysis_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.watchlist import router as watchlist_router

__all__ = ["analysis_router", "alerts_router", "watchlist_router"]
