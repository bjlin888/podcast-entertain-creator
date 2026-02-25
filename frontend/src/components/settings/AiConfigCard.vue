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
        <span>LLM API Key</span>
        <input class="inp" v-model="settings.llmKey" type="password" placeholder="sk-..." />
      </label>
      <label class="form-field">
        <span>TTS 供應商</span>
        <select class="inp" v-model="settings.ttsProvider">
          <option value="gemini">Gemini AI 語音 (推薦)</option>
          <option value="google">Google Cloud TTS</option>
        </select>
      </label>
      <label class="form-field">
        <span>TTS API Key</span>
        <input class="inp" v-model="settings.ttsKey" type="password" />
      </label>
    </div>
    <button class="btn-teal save-btn" @click="settings.saveAll()">儲存 AI 設定</button>
  </div>
</template>

<script setup>
import { useSettingsStore } from '../../stores/settings'

const settings = useSettingsStore()

function onProviderChange() {
  const models = settings.getLLMModels()
  if (!models.includes(settings.llmModel)) {
    settings.llmModel = models[0]
  }
}
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
}
.save-btn {
  margin-top: 4px;
}

@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
