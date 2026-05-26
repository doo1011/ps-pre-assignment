const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(BASE + path, options)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? '요청 실패')
  }
  return res.json()
}

export const api = {
  // 잡 목록
  getJobs: (page = 1, size = 20) =>
    request(`/excel/jobs?page=${page}&size=${size}`),

  // 엑셀 생성 요청 (날짜 범위 선택적)
  generateExcel: ({ startDate, endDate } = {}) =>
    request('/excel/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        start_date: startDate || null,
        end_date:   endDate   || null,
      }),
    }),

  // 다운로드 URL
  downloadUrl: (jobId) => `${BASE}/excel/download/${jobId}`,

  // 주문 목록
  getOrders: (page = 1, size = 20) =>
    request(`/orders?page=${page}&size=${size}`),

  // 주문 날짜 범위 (min/max)
  getDateRange: () =>
    request('/orders/date-range'),
}
