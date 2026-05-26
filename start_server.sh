#!/bin/bash
set -e

echo "======================================"
echo "  Excel Generator - 서버 시작 스크립트"
echo "======================================"

# 1. DB 컨테이너 시작
echo ""
echo "[1/5] DB 컨테이너 시작..."
docker compose up db -d

# 2. DB healthy 대기
echo "[2/5] DB 준비 대기 중..."
until docker compose exec db pg_isready -U excel_user -d excel_db -q; do
  sleep 1
done
echo "      DB 준비 완료"

# 3. 테이블 생성
echo "[3/5] 테이블 생성..."
docker compose exec -T db psql -U excel_user -d excel_db \
  -c "$(cat backend/orders.sql)"
docker compose exec -T db psql -U excel_user -d excel_db \
  -c "$(cat backend/jobs.sql)"
echo "      테이블 생성 완료"

# 4. 샘플 데이터 삽입 (orders 테이블이 비어있을 때만)
echo "[4/5] 샘플 데이터 확인..."
COUNT=$(docker compose exec -T db psql -U excel_user -d excel_db -tAc \
  "SELECT COUNT(*) FROM public.orders")
if [ "$COUNT" -eq "0" ]; then
  echo "      orders 테이블이 비어있습니다. 샘플 데이터 10만 건 삽입 중..."
  cd backend && python scripts/seed_orders.py && cd ..
  echo "      샘플 데이터 삽입 완료"
else
  echo "      이미 ${COUNT}건 존재 — 삽입 건너뜀"
fi

# 5. 전체 서비스 빌드 & 실행
echo "[5/5] API 및 프론트엔드 빌드 & 시작..."
docker compose --profile app up -d --build

echo ""
echo "======================================"
echo "  실행 완료"
echo "  프론트엔드 : http://localhost"
echo "  API 문서   : http://localhost:8000/docs"
echo "======================================"
