from fastapi import APIRouter

from .endpoints import accounts, sites, sync_jobs, users


api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(sites.router, prefix="/sites", tags=["sites"])
api_router.include_router(sync_jobs.router, prefix="/sync-jobs", tags=["sync-jobs"])


__all__ = ["api_router"]
