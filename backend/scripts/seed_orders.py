"""
orders 테이블 샘플 데이터 생성 스크립트
사용법: python seed_orders.py
"""
import asyncio
import asyncpg
import random
from datetime import datetime, timedelta

# ── 연결 설정 ───────────────────────────────────────────────
DB_DSN = "postgresql://excel_user:excel_pass@localhost:5432/excel_db"

TOTAL_ROWS = 150_000
CHUNK_SIZE = 2_000   # 한 번에 insert할 건수

# ── 샘플 데이터 ──────────────────────────────────────────────
USER_NAMES = [
    "김민준", "이서연", "박도현", "최지우", "정예준",
    "강서현", "윤시우", "장하은", "임준서", "한소율",
    "오지호", "신유진", "권태양", "황나연", "송민재",
    "홍수빈", "문지훈", "배아름", "노현우", "조은서",
]

CATEGORIES = {
    "스키/스노보드": ["알파인스키 1일권", "스노보드 풀패키지", "야간 스키권", "리프트 시즌권", "스키 장비 렌탈"],
    "워터파크":      ["종일 자유이용권", "패밀리 패키지", "캐빈 숙박+입장권", "익스프레스 패스", "야간 개장권"],
    "숙박":          ["스탠다드 룸", "디럭스 룸", "패밀리 스위트", "풀빌라", "글램핑 패키지"],
    "테마파크":      ["1일 이용권", "연간 회원권", "패스트트랙 패키지", "그룹 할인권", "야간 프리미엄권"],
    "레저/액티비티": ["번지점프", "ATV 체험", "래프팅 패키지", "짚라인", "카약 투어", "패러글라이딩"],
    "여행패키지":    ["제주 2박3일", "강원도 스키+숙박", "부산 1박2일", "해외 골프 투어", "가족 리조트 패키지"],
}

STATUSES = ["CONFIRMED", "CANCELLED", "PENDING"]

BASE_DATE = datetime.now() - timedelta(days=365 * 2)  # 최근 2년치 데이터


def random_row() -> tuple:
    category = random.choice(list(CATEGORIES.keys()))
    product  = random.choice(CATEGORIES[category])
    order_date = BASE_DATE + timedelta(
        seconds=random.randint(0, 365 * 2 * 24 * 3600)
    )
    return (
        random.choice(USER_NAMES),          # user_name
        product,                            # product_name
        category,                           # category
        random.randint(10_000, 1_500_000),  # amount (원)
        random.choice(STATUSES),            # status
        order_date,                         # order_date
    )


# ── DDL ─────────────────────────────────────────────────────
DDL = """
CREATE TABLE IF NOT EXISTS public.orders (
    id           bigserial  NOT NULL,
    user_name    varchar    NULL,
    product_name varchar    NULL,
    category     varchar    NULL,
    amount       int4       NULL,
    status       varchar    NULL,
    order_date   timestamp  NULL
);
"""

INSERT_SQL = """
    INSERT INTO public.orders (user_name, product_name, category, amount, status, order_date)
    VALUES ($1, $2, $3, $4, $5, $6)
"""


# ── 메인 ─────────────────────────────────────────────────────
async def seed():
    print(f"DB 연결 중... ({DB_DSN})")
    pool = await asyncpg.create_pool(DB_DSN, min_size=1, max_size=3)

    async with pool.acquire() as conn:
        await conn.execute(DDL)
        print("테이블 확인 완료")

    inserted   = 0
    start_time = datetime.now()

    while inserted < TOTAL_ROWS:
        chunk_size = min(CHUNK_SIZE, TOTAL_ROWS - inserted)
        rows = [random_row() for _ in range(chunk_size)]

        async with pool.acquire() as conn:
            await conn.executemany(INSERT_SQL, rows)

        inserted += chunk_size
        elapsed   = (datetime.now() - start_time).total_seconds()
        print(f"  {inserted:>7,} / {TOTAL_ROWS:,}  ({elapsed:.1f}s)")

    total_elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n완료: {inserted:,}건 삽입 — {total_elapsed:.1f}초")

    await pool.close()


if __name__ == "__main__":
    asyncio.run(seed())
