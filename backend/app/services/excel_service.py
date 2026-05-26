import asyncio
import os
from datetime import datetime
from pathlib import Path

import xlsxwriter

from app.config import settings
from app.constants import ORDER_STATUS_MAP
from app.db.connection import get_pool
from app.db.job_crud import update_job
from app.worker.queue import executor

HEADERS = ["ID", "주문자명", "상품명", "카테고리", "금액(원)", "상태", "주문일시"]


# ── 동기 함수: ThreadPoolExecutor에서 실행 ──────────────────────
def _write_excel(file_path: str, rows: list[tuple]) -> None:
    Path(os.path.dirname(file_path)).mkdir(parents=True, exist_ok=True)

    workbook  = xlsxwriter.Workbook(file_path, {"constant_memory": True})
    worksheet = workbook.add_worksheet("주문목록")

    # 헤더 스타일
    bold = workbook.add_format({"bold": True, "bg_color": "#D9E1F2"})
    for col, header in enumerate(HEADERS):
        worksheet.write(0, col, header, bold)

    # 데이터 행
    for row_idx, row in enumerate(rows, start=1):
        worksheet.write(row_idx, 0, row[0])                                  # id
        worksheet.write(row_idx, 1, row[1])                                  # user_name
        worksheet.write(row_idx, 2, row[2])                                  # product_name
        worksheet.write(row_idx, 3, row[3])                                  # category
        worksheet.write(row_idx, 4, row[4])                                  # amount
        worksheet.write(row_idx, 5, ORDER_STATUS_MAP.get(row[5], row[5]))     # status
        worksheet.write(row_idx, 6, str(row[6]))                             # order_date

    workbook.close()


# ── 비동기 메인 처리 ────────────────────────────────────────────
async def process_excel_job(job_id: str) -> None:
    pool = await get_pool()

    try:
        # 1. PROCESSING 시작 + started_at 기록
        async with pool.acquire() as conn:
            await update_job(conn, job_id, status="PROCESSING", progress=10, started_at=datetime.now())

        # 2. DB에서 주문 데이터 조회
        async with pool.acquire() as conn:
            records = await conn.fetch(
                """
                SELECT id, user_name, product_name, category, amount, status, order_date
                FROM public.orders
                ORDER BY id
                """
            )

        # Record → tuple 변환 (스레드 간 전달 시 안전)
        rows = [tuple(r) for r in records]

        async with pool.acquire() as conn:
            await update_job(conn, job_id, progress=50)

        # 3. Excel 파일 생성 (동기 작업 → 스레드 풀로 위임)
        file_path = f"{settings.excel_output_dir}/{job_id}.xlsx"
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(executor, _write_excel, file_path, rows)

        # 4. 완료 + completed_at 기록
        async with pool.acquire() as conn:
            await update_job(conn, job_id, status="COMPLETED", progress=100, file_path=file_path, completed_at=datetime.now())

    except Exception as e:
        async with pool.acquire() as conn:
            await update_job(conn, job_id, status="FAILED", error=str(e), completed_at=datetime.now())
        raise
