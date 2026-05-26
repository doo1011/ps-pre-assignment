import uuid

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.constants import JOB_STATUS_MAP
from app.db.connection import get_pool
from app.db.job_crud import create_job, get_job
from app.worker.queue import job_queue

router = APIRouter(prefix="/api/excel", tags=["excel"])


# ── 1. 엑셀 생성 요청 ────────────────────────────────────────────
@router.post("/generate", status_code=202)
async def generate_excel():
    """
    엑셀 생성 작업을 요청합니다.
    즉시 job_id를 반환하고, 백그라운드에서 파일을 생성합니다.
    """
    job_id = str(uuid.uuid4())
    pool   = await get_pool()

    async with pool.acquire() as conn:
        await create_job(conn, job_id)

    await job_queue.put(job_id)

    return {"job_id": job_id, "status": JOB_STATUS_MAP["PENDING"]}


# ── 2. 작업 상태 조회 ────────────────────────────────────────────
@router.get("/status/{job_id}")
async def get_status(job_id: str):
    """
    job_id에 해당하는 작업의 진행 상태를 반환합니다.
    status: PENDING | PROCESSING | COMPLETED | FAILED
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        job = await get_job(conn, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id":       job["id"],
        "status":       JOB_STATUS_MAP.get(job["status"], job["status"]),
        "progress":     job["progress"],
        "error":        job["error"],
        "created_at":   job["created_at"],
        "started_at":   job["started_at"],
        "completed_at": job["completed_at"],
    }


# ── 3. 엑셀 파일 다운로드 ────────────────────────────────────────
@router.get("/download/{job_id}")
async def download_excel(job_id: str):
    """
    완료된 엑셀 파일을 다운로드합니다.
    COMPLETED 상태가 아니면 400을 반환합니다.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        job = await get_job(conn, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail=f"파일 준비 중입니다. 현재 상태: {job['status']} ({job['progress']}%)",
        )

    return FileResponse(
        path=job["file_path"],
        filename=f"orders_{job_id[:8]}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ── 4. 잡 목록 조회 ──────────────────────────────────────────────
@router.get("/jobs")
async def list_jobs(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    """
    엑셀 생성 요청 목록을 최신순으로 반환합니다.
    """
    offset = (page - 1) * size
    pool   = await get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, status, file_path, created_at, started_at, completed_at
            FROM jobs
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """,
            size, offset,
        )
        total = await conn.fetchval("SELECT COUNT(*) FROM jobs")

    return {
        "total": total,
        "page":  page,
        "size":  size,
        "items": [
            {
                "job_id":       r["id"],
                "status":       JOB_STATUS_MAP.get(r["status"], r["status"]),
                "file_path":    r["file_path"],
                "created_at":   r["created_at"],
                "started_at":   r["started_at"],
                "completed_at": r["completed_at"],
            }
            for r in rows
        ],
    }
