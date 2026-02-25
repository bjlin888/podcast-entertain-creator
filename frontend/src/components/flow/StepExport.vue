<template>
  <div class="step-export anim-rise">
    <div class="success-circle">🎉</div>
    <h1 class="step-h1">腳本完成！</h1>
    <p class="step-sub">你的 Podcast 腳本已經準備好了。</p>

    <div class="script-box">
      <pre class="script-text">{{ flow.fullScript || '載入中...' }}</pre>
    </div>

    <div class="export-actions">
      <button class="btn-primary" @click="handleCopy">
        📋 複製腳本
      </button>
      <button class="btn-secondary" @click="flow.downloadScript()">
        💾 下載 .txt 檔
      </button>
    </div>

    <hr class="divider" />

    <div class="nav-actions">
      <button class="btn-secondary" @click="$emit('back-to-list')">
        ← 回到集數列表
      </button>
      <button class="btn-teal" @click="$emit('new-episode')">
        ＋ 新的一集
      </button>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useFlowStore } from '../../stores/flow'
import { useToast } from '../../composables/useToast'

const flow = useFlowStore()
const toast = useToast()

defineEmits(['back-to-list', 'new-episode'])

onMounted(() => {
  if (!flow.fullScript) {
    flow.buildFullScript()
  }
})

function handleCopy() {
  flow.copyScript()
  toast.show('腳本已複製到剪貼簿！')
}
</script>

<style scoped>
.step-export {
  text-align: center;
}
.step-h1 {
  font-family: var(--font-display);
  font-size: 30px;
  font-weight: 700;
  margin-bottom: 8px;
}
.step-sub {
  font-size: 15px;
  color: var(--gray-mid);
  margin-bottom: 24px;
}
.script-box {
  background: var(--warm-white);
  border: 1.5px solid var(--gray-light);
  border-radius: var(--radius-sm);
  padding: 20px;
  max-height: 320px;
  overflow-y: auto;
  text-align: left;
  margin-bottom: 20px;
}
.script-text {
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: var(--ink);
}
.export-actions {
  display: flex;
  gap: 11px;
  margin-bottom: 0;
}
.export-actions .btn-primary {
  flex: 1;
}
.export-actions .btn-secondary {
  flex: 1;
}
.nav-actions {
  display: flex;
  gap: 11px;
  justify-content: center;
}
</style>
