<template>
  <div class="card">
    <div class="card-header">
      <span class="card-title">데이터 요청 목록</span>
      <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
        <input type="date" v-model="startDate" class="date-input" />
        <span style="color:#999;">~</span>
        <input type="date" v-model="endDate" class="date-input" />
        <button class="btn btn-primary" :disabled="generating" @click="requestGenerate">
          {{ generating ? '요청 중...' : '+ 엑셀 생성 요청' }}
        </button>
        <button class="btn" style="border:1px solid #ddd;" @click="load">새로고침</button>
      </div>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Job ID</th>
            <th>요청일시</th>
            <th>시작시간</th>
            <th>완료시간</th>
            <th>상태</th>
            <th>파일</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="6" style="text-align:center; color:#999; padding:32px;">불러오는 중...</td>
          </tr>
          <tr v-else-if="items.length === 0">
            <td colspan="6" style="text-align:center; color:#999; padding:32px;">요청 내역이 없습니다.</td>
          </tr>
          <tr v-for="job in items" :key="job.job_id">
            <td style="font-family:monospace; font-size:12px; color:#666;">{{ job.job_id.slice(0, 8) }}…</td>
            <td>{{ fmt(job.created_at) }}</td>
            <td>{{ fmt(job.started_at) }}</td>
            <td>{{ fmt(job.completed_at) }}</td>
            <td><span :class="badgeClass(job.status)">{{ job.status }}</span></td>
            <td>
              <a v-if="job.status === '완료'" :href="downloadUrl(job.job_id)" class="btn btn-sm btn-primary">
                다운로드
              </a>
              <span v-else style="color:#bbb;">-</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pagination">
      <span>총 {{ total }}건</span>
      <button class="page-btn" :disabled="page <= 1" @click="changePage(page - 1)">‹</button>
      <button class="page-btn active">{{ page }}</button>
      <button class="page-btn" :disabled="page >= totalPages" @click="changePage(page + 1)">›</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api.js'

const emit = defineEmits(['toast'])

const items      = ref([])
const total      = ref(0)
const page       = ref(1)
const loading    = ref(false)
const generating = ref(false)
const startDate  = ref('')
const endDate    = ref('')
const SIZE       = 20

const totalPages = computed(() => Math.ceil(total.value / SIZE))

async function load() {
  loading.value = true
  try {
    const data = await api.getJobs(page.value, SIZE)
    items.value = data.items
    total.value = data.total
  } catch (e) {
    emit('toast', { msg: e.message, type: 'error' })
  } finally {
    loading.value = false
  }
}

async function requestGenerate() {
  generating.value = true
  try {
    const data = await api.generateExcel({
      startDate: startDate.value || null,
      endDate:   endDate.value   || null,
    })
    emit('toast', { msg: `생성 요청 완료 (${data.job_id.slice(0, 8)}…)`, type: 'success' })
    page.value = 1
    await load()
  } catch (e) {
    emit('toast', { msg: e.message, type: 'error' })
  } finally {
    generating.value = false
  }
}

function changePage(p) { page.value = p; load() }
function downloadUrl(jobId) { return api.downloadUrl(jobId) }

function fmt(val) {
  if (!val) return '-'
  const d = new Date(val)
  const y   = d.getFullYear()
  const mo  = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h   = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  const s   = String(d.getSeconds()).padStart(2, '0')
  return `${y}년 ${mo}월 ${day}일 ${h}:${min}:${s}`
}

function badgeClass(status) {
  const map = { '대기 중': 'badge badge-pending', '생성 중': 'badge badge-processing', '완료': 'badge badge-done', '실패': 'badge badge-failed' }
  return map[status] ?? 'badge'
}

onMounted(load)
</script>

<style scoped>
.date-input {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  color: #333;
}
</style>
