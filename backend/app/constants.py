# 주문 상태 (orders.status)
ORDER_STATUS_MAP: dict[str, str] = {
    "CONFIRMED": "주문 완료",
    "CANCELLED": "주문 취소",
    "PENDING":   "주문 대기",
}

# 잡 상태 (jobs.status)
JOB_STATUS_MAP: dict[str, str] = {
    "PENDING":    "대기 중",
    "PROCESSING": "생성 중",
    "COMPLETED":  "완료",
    "FAILED":     "실패",
}
