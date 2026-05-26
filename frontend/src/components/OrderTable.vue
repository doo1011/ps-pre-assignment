<template>
  <div class="card">
    <div class="card-header">
      <span class="card-title">주문 목록</span>
      <span style="font-size:12px; color:#999;">총 {{ total.toLocaleString() }}건</span>
    </div>

    <!-- 날짜 범위 안내 -->
    <div v-if="dateRange.min_date" style="font-size:12px; color:#666; margin-bottom:14px;">
      📅 데이터 범위: <b>{{ fmtDate(dateRange.min_date) }}</b> ~ <b>{{ fmtDate(dateRange.max_date) }}</b>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>주문자명</th>
            <th>상품명</th>
            <th>카테고리</th>
            <th style="text-align:right;">금액</th>
            <th>상태</th>
            <th>주문일시</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" style="text-align:center; color:#999; padding:32px;">불러오는 중...</td>
          </tr>
          <tr v-for="row in items" :key="row.id">
            <td style="color:#999;">{{ row.id }}</td>
            <td>{{ row.user_name }}</td>
            <td>{{ row.product_name }}</td>
            <td>{{ row.category }}</td>
            <td style="text-align:right; font-variant-numeric: tabular-nums;">
              {{ row.amount.toLocaleString() }}원
            </td>
            <td>{{ row.status }}</td>
            <td>{{ fmt(row.order_date) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pagination">
      <button class="page-btn" :disabled="page <= 1" @click="changePage(page - 1)">‹</button>
      <span>{{ page }} / {{ totalPages }}</span>
      <button class="page-btn" :disabled="page >= totalPages" @click="changePage(page + 1)">›</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api.js'

const emit = defineEmits(['toast'])

const items     = ref([])
const total     = ref(0)
const page      = ref(1)
const loading   = ref(false)
const dateRange = ref({ min_date: null, max_date: null })
const SIZE      = 20

const totalPages = computed(() => Math.ceil(total.value / SIZE))

async function load() {
  loading.value = true
  try {
    const data = await api.getOrders(page.value, SIZE)
    items.value = data.items
    total.value = data.total
  } catch (e) {
    emit('toast', { msg: e.message, type: 'error' })
  } finally {
    loading.value = false
  }
}

async function loadDateRange() {
  try {
    dateRange.value = await api.getDateRange()
  } catch { /* 조용히 무시 */ }
}

function changePage(p) { page.value = p; load() }

function fmt(val) {
  if (!val) return '-'
  const d   = new Date(val)
  const y   = d.getFullYear()
  const mo  = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h   = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  const s   = String(d.getSeconds()).padStart(2, '0')
  return `${y}년 ${mo}월 ${day}일 ${h}:${min}:${s}`
}

// 날짜 범위 표시용 (날짜만)
function fmtDate(val) {
  if (!val) return '-'
  const d   = new Date(val)
  const y   = d.getFullYear()
  const mo  = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}년 ${mo}월 ${day}일`
}

onMounted(() => { load(); loadDateRange() })
</script>
