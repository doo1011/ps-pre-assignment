# ps-pre-assignment

사용자가 엑셀 생성을 요청하면 즉시 응답을 반환하고, 백그라운드에서 10만 건의 데이터를 엑셀 파일로 생성하는 비동기 처리 시스템입니다.

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | FastAPI, asyncpg, xlsxwriter |
| Database | PostgreSQL 16 |
| Frontend | Vue 3 + Vite, nginx |
| Infra | Docker Compose |

---

## 프로젝트 구조

```
ps-pre-assignment/
├── docker-compose.yml
├── start_server.sh          # 초기 설정 + 실행 스크립트
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── orders.sql           # 주문 테이블 DDL
│   ├── jobs.sql             # 잡 테이블 DDL
│   ├── scripts/
│   │   └── seed_orders.py   # 샘플 데이터 생성 스크립트
│   └── app/
│       ├── main.py          # FastAPI 앱 진입점, 워커 시작
│       ├── config.py        # 환경변수 설정
│       ├── constants.py     # 상태값 한글 매핑
│       ├── api/
│       │   ├── excel_router.py   # 엑셀 생성 관련 API
│       │   └── orders_router.py  # 주문 목록 API
│       ├── db/
│       │   ├── connection.py     # asyncpg 커넥션 풀
│       │   └── job_crud.py       # jobs 테이블 CRUD
│       ├── services/
│       │   └── excel_service.py  # 엑셀 생성 비즈니스 로직
│       └── worker/
│           └── queue.py          # asyncio.Queue + ThreadPoolExecutor
└── frontend/
    ├── Dockerfile
    ├── nginx.conf           # /api 프록시 + SPA fallback
    ├── vite.config.js
    └── src/
        ├── api.js
        ├── App.vue
        └── components/
            ├── JobTable.vue     # 요청 목록 + 엑셀 생성 버튼
            └── OrderTable.vue   # 주문 목록 페이지네이션
```

---

## API 목록

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/excel/generate` | 엑셀 생성 요청 (202 즉시 반환) |
| GET | `/api/excel/status/{job_id}` | 잡 상태 조회 |
| GET | `/api/excel/download/{job_id}` | 완료된 파일 다운로드 |
| GET | `/api/excel/jobs` | 잡 목록 페이지네이션 |
| GET | `/api/orders` | 주문 목록 페이지네이션 |

---

## 비동기 처리 구조

```
[요청]
  │
  ▼
POST /api/excel/generate
  ├── jobs 테이블 INSERT (status=PENDING)
  ├── asyncio.Queue.put(job_id)
  └── 202 즉시 반환

[백그라운드]
asyncio Worker (1개)
  ├── Queue.get()
  ├── status → PROCESSING, started_at 기록
  ├── orders 테이블 전체 조회 (asyncpg)
  ├── xlsxwriter로 엑셀 파일 생성 (ThreadPoolExecutor)
  └── status → COMPLETED, completed_at, file_path 기록
```

---

## 실행 방법

```bash
bash start_server.sh
```

- 프론트엔드: http://localhost
- API 문서: http://localhost:8000/docs

### 개발 환경 실행

```bash
# DB만 실행
docker compose up db -d

# 백엔드 로컬 실행
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 프론트엔드 로컬 실행
cd frontend
npm install && npm run dev
```

### 유용한 명령어

```bash
# 로그 확인
docker compose logs -f api
docker compose logs -f frontend

# 재빌드
docker compose --profile app up -d --build

# 전체 종료
docker compose --profile app down
```

---

## 설계 결정 사항

### 1. FastAPI 선택
- 단일 컨테이너 제약(0.5 CPU, 512M)에서 Spring Boot 대비 기본 메모리 사용량이 낮음
- asyncio 기반으로 비동기 처리에 자연스럽게 적합

### 2. ORM 없이 asyncpg 직접 연결
- 10만 건 배치 INSERT 성능을 위해 SQLAlchemy 레이어 없이 asyncpg 직접 사용
- `executemany()`로 1,000건 단위 청크 INSERT

### 3. SQLite 대신 PostgreSQL
- 10만 건 데이터를 DB에 저장하는 요구사항에서 SQLite는 쓰기 직렬화 문제 발생
- 단일 컨테이너 제약은 백엔드(api) 기준이므로 DB 컨테이너는 별도 허용

### 4. 워커 1개 운영
- 0.5 CPU 환경에서 워커 N개를 동시 실행해도 총 처리량(jobs/시간)은 동일
- 워커 1개가 0.5 CPU를 독점 사용하여 단일 잡 처리 속도 최적화
- asyncio 이벤트 루프는 단일 스레드로 동작하므로 워커 수와 무관하게 API 응답성 유지

### 5. xlsxwriter constant_memory 모드
- 512M 메모리 제약에서 10만 행을 한 번에 메모리에 올리지 않고 행 단위 즉시 디스크 flush
- openpyxl 대비 메모리 사용량 약 1/5

### 6. asyncio.Queue + ThreadPoolExecutor 구조
- Excel 쓰기(CPU-bound)는 ThreadPoolExecutor에서 실행하여 이벤트 루프 블로킹 방지
- DB 조회(I/O-bound)는 asyncpg로 이벤트 루프 안에서 처리
- Queue로 동시 처리 수 제한 → 메모리 예산 보호

### 7. 잡 상태 관리 — In-memory Queue + DB 분리
- asyncio.Queue: 실제 작업 큐 (메모리)
- jobs 테이블: 상태 추적 및 클라이언트 조회용
- Queue는 조회 불가능하므로 DB에 상태를 별도 기록

### 8. 프론트 상태 확인 — 페이지 새로고침
- 폴링(n초마다 요청) 또는 SSE 대신 수동 새로고침 선택
- 과제 규모에서 복잡도 대비 실용성 고려

### 9. KST 시간 저장
- `datetime.now(KST).replace(tzinfo=None)` 방식으로 KST 기준 naive datetime 저장
- DB 컬럼이 `TIMESTAMP` (without timezone)이므로 tzinfo 제거 후 저장
