from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI

from api.routes import router as api_router
from api.sync_service import run_sync_once

scheduler = AsyncIOScheduler(timezone=ZoneInfo("Europe/Moscow"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler.add_job(
        run_sync_once,
        trigger=CronTrigger(hour=3, minute=0),
        id="events_daily_sync",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)

app.include_router(api_router, prefix="/api", tags=["api"])
