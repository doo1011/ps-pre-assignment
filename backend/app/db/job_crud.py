import asyncpg


async def create_job(conn: asyncpg.Connection, job_id: str) -> None:
    await conn.execute(
        "INSERT INTO jobs (id) VALUES ($1)",
        job_id,
    )


async def get_job(conn: asyncpg.Connection, job_id: str) -> asyncpg.Record | None:
    return await conn.fetchrow("SELECT * FROM jobs WHERE id = $1", job_id)


async def update_job(conn: asyncpg.Connection, job_id: str, **kwargs) -> None:
    set_clause = ", ".join(f"{k} = ${i + 2}" for i, k in enumerate(kwargs))
    await conn.execute(
        f"UPDATE jobs SET {set_clause} WHERE id = $1",
        job_id,
        *kwargs.values(),
    )
