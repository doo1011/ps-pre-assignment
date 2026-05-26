from fastapi import APIRouter, Query

from app.constants import ORDER_STATUS_MAP
from app.db.connection import get_pool

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("/date-range")
async def get_date_range():
    """주문 데이터의 최소/최대 주문일시를 반환합니다."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT MIN(order_date) AS min_date, MAX(order_date) AS max_date FROM public.orders"
        )
    return {"min_date": row["min_date"], "max_date": row["max_date"]}


@router.get("")
async def list_orders(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    """주문 목록을 주문일시 내림차순으로 반환합니다."""
    offset = (page - 1) * size
    pool   = await get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, user_name, product_name, category, amount, status, order_date
            FROM public.orders
            ORDER BY order_date DESC
            LIMIT $1 OFFSET $2
            """,
            size, offset,
        )
        total = await conn.fetchval("SELECT COUNT(*) FROM public.orders")

    return {
        "total": total,
        "page":  page,
        "size":  size,
        "items": [
            {
                **dict(r),
                "status": ORDER_STATUS_MAP.get(r["status"], r["status"]),
            }
            for r in rows
        ],
    }
