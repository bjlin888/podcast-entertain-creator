<template>
  <div class="card">
    <div class="card-label">🤖 AI 設定</div>
    <div class="form-grid">
      <label class="form-field">
        <span>LLM 供應商</span>
        <select class="inp" v-model="settings.llmProvider" @change="onProviderChange">
          <option value="claude">Claude (Anthropic)</option>
          <option value="gemini">Gemini (Google)</option>
        </select>
      </label>
      <label class="form-field">
        <span>模型</span>
        <select class="inp" v-model="settings.llmModel">
          <option v-for="m in settings.getLLMModels()" :key="m" :value="m">{{ m }}</option>
        </select>
      </label>
      <label class="form-field full">
        <span>
          LLM API Key
          <span v-if="currentProviderHasKey" class="key-badge saved">已設定</span>
        </span>
        <input
          class="inp"
          v-model="settings.llmKey"
          type="password"
          :placeholder="currentProviderHasKey ? '已儲存（輸入新值可覆蓋）' : 'sk-...'"
        />
      </label>
      <label class="form-field">
        <span>TTS 供應商</span>
        <select class="inp" v-model="settings.ttsProvider">
          <option value="gemini">Gemini AI 語音 (推薦)</option>
          <option value="google">Google Cloud TTS</option>
        </select>
      </label>
      <label class="form-field">
        <span>
          TTS API Key
          <span v-if="settings.hasGeminiKey && settings.ttsProvider === 'gemini'" class="key-badge saved">共用 Gemini Key</span>
        </span>
        <input
          class="inp"
          v-model="settings.ttsKey"
          type="password"
          :placeholder="settings.ttsProvider === 'gemini' ? '與 LLM 共用（可留空）' : 'API Key'"
          :disabled="settings.ttsProvider === 'google'"
        />
      </label>
    </div>
    <div class="btn-row">
      <button
        class="btn-teal save-btn"
        @click="handleSave"
        :disabled="settings.aiSaving"
      >
        {{ settings.aiSaving ? '儲存中...' : '儲存 AI 設定' }}
      </button>
      <span v-if="saveResult === 'ok'" class="save-msg ok">已儲存</span>
      <span v-else-if="saveResult === 'fail'" class="save-msg fail">儲存失敗，請確認 ENCRYPTION_KEY 已設定</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useSettingsStore } from '../../stores/settings'

const settings = useSettingsStore()
const saveResult = ref('')

const currentProviderHasKey = computed(() => {
  if (settings.llmProvider === 'gemini') return settings.hasGeminiKey
  if (settings.llmProvider === 'claude') return settings.hasClaudeKey
  return false
})

function onProviderChange() {
  const models = settings.getLLMModels()
  if (!models.includes(settings.llmModel)) {
    settings.llmModel = models[0]
  }
}

async function handleSave() {
  saveResult.value = ''
  const ok = await settings.saveAiSettings()
  saveResult.value = ok ? 'ok' : 'fail'
  setTimeout(() => { saveResult.value = '' }, 3000)
}

onMounted(() => {
  settings.loadAiSettings()
})
</script>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 16px;
}
.form-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.form-field.full {
  grid-column: 1 / -1;
}
.form-field span {
  font-size: 12px;
  font-weight: 700;
  color: var(--gray-mid);
  display: flex;
  align-items: center;
  gap: 6px;
}
.key-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 8px;
}
.key-badge.saved {
  background: var(--teal);
  color: white;
}
.btn-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
}
.save-msg {
  font-size: 13px;
  font-weight: 600;
}
.save-msg.ok { color: var(--teal); }
.save-msg.fail { color: var(--error); }

@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
