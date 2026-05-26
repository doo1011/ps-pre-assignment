import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db.connection import close_pool, get_pool
from app.api.excel_router import router
from app.api.orders_router import router as orders_router
from app.services.excel_service import process_excel_job
from app.worker.queue import job_queue


# ── 백그라운드 워커 ──────────────────────────────────────────────
async def worker() -> None:
    """큐에서 job_id를 꺼내 엑셀 생성 작업을 처리합니다."""
    while True:
        job_id = await job_queue.get()
        try:
            await process_excel_job(job_id)
        except Exception as e:
            print(f"[worker] job {job_id} failed: {e}")
        finally:
            job_queue.task_done()


# ── 앱 생명주기 ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작
    await get_pool()

    # 워커 N개 동시 실행 (= 최대 동시 처리 가능한 작업 수)
    workers = [
        asyncio.create_task(worker())
        for _ in range(settings.max_concurrent_jobs)
    ]
    print(f"[app] {settings.max_concurrent_jobs}개 워커 시작")

    yield

    # 종료
    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)
    await close_pool()
    print("[app] 종료")


# ── FastAPI 앱 ───────────────────────────────────────────────────
app = FastAPI(
    title="Excel Generator API",
    lifespan=lifespan,
)

app.include_router(router)
app.include_router(orders_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
