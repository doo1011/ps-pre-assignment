<template>
  <div class="container">
    <h1 style="font-size:20px; font-weight:700; margin-bottom:24px;">📊 Excel Generator</h1>

    <JobTable @toast="showToast" />
    <OrderTable @toast="showToast" />
  </div>

  <Transition name="fade">
    <div v-if="toast.visible" :class="['toast', toast.type]">
      {{ toast.msg }}
    </div>
  </Transition>
</template>

<script setup>
import { reactive } from 'vue'
import JobTable   from './components/JobTable.vue'
import OrderTable from './components/OrderTable.vue'

const toast = reactive({ visible: false, msg: '', type: '' })
let toastTimer = null

function showToast({ msg, type = '' }) {
  if (toastTimer) clearTimeout(toastTimer)
  toast.msg     = msg
  toast.type    = type
  toast.visible = true
  toastTimer = setTimeout(() => { toast.visible = false }, 3000)
}
</script>

<style>
.fade-enter-active, .fade-leave-active { transition: opacity .2s; }
.fade-enter-from, .fade-leave-to       { opacity: 0; }
</style>
