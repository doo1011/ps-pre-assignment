import asyncio
from concurrent.futures import ThreadPoolExecutor

# 작업 큐 — {job_id, start_date, end_date} 딕셔너리를 담는다
job_queue: asyncio.Queue[dict] = asyncio.Queue()

# Excel 파일 쓰기(동기)를 처리할 스레드 풀
# 워커 1개 → 스레드 1개 → 0.5 CPU 독점 사용
executor = ThreadPoolExecutor(max_workers=1)
