<template>
  <div class="card">
    <div class="plat-header">
      <div class="plat-info">
        <span class="plat-logo">{{ platform === 'google' ? '🟢' : '🍎' }}</span>
        <div>
          <div class="plat-name">{{ platform === 'google' ? 'Google Podcasts' : 'Apple Podcasts' }}</div>
          <div class="plat-desc">{{ platform === 'google' ? 'RSS Feed 同步' : 'API 金鑰連線' }}</div>
        </div>
      </div>
      <div class="plat-right">
        <span class="plat-status" :class="statusClass">{{ statusLabel }}</span>
        <ToggleSwitch v-model="enabled" />
      </div>
    </div>

    <template v-if="enabled">
      <hr class="divider" />
      <div class="form-grid">
        <template v-if="platform === 'google'">
          <label class="form-field full">
            <span>RSS Feed URL</span>
            <input class="inp" v-model="settings.googleRss" placeholder="https://feeds.example.com/podcast" />
          </label>
          <label class="form-field">
            <span>驗證碼</span>
            <input class="inp" v-model="settings.googleVerify" />
          </label>
          <label class="form-field">
            <span>更新間隔</span>
            <select class="inp" v-model="settings.googleInterval">
              <option value="auto">自動</option>
              <option value="daily">每天</option>
              <option value="weekly">每週</option>
            </select>
          </label>
        </template>
        <template v-else>
          <label class="form-field">
            <span>Apple ID</span>
            <input class="inp" v-model="settings.appleId" />
          </label>
          <label class="form-field">
            <span>Provider ID</span>
            <input class="inp" v-model="settings.appleProviderId" />
          </label>
          <label class="form-field full">
            <span>API Key</span>
            <input class="inp" v-model="settings.appleKey" type="password" />
          </label>
          <label class="form-field">
            <span>Key ID</span>
            <input class="inp" v-model="settings.appleKeyId" />
          </label>
          <label class="form-field">
            <span>Team ID</span>
            <input class="inp" v-model="settings.appleTeamId" />
          </label>
          <label class="form-field full">
            <span>RSS Feed URL</span>
            <input class="inp" v-model="settings.appleRss" placeholder="https://..." />
          </label>
        </template>
      </div>

      <div class="plat-actions">
        <button class="btn-teal" @click="settings.saveAll()">儲存</button>
        <button class="btn-secondary">測試連線</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSettingsStore } from '../../stores/settings'
import ToggleSwitch from './ToggleSwitch.vue'

const props = defineProps({
  platform: { type: String, required: true },
})

const settings = useSettingsStore()

const enabled = computed({
  get: () => props.platform === 'google' ? settings.googleEnabled : settings.appleEnabled,
  set: (v) => {
    if (props.platform === 'google') settings.googleEnabled = v
    else settings.appleEnabled = v
  },
})

const status = computed(() => {
  return props.platform === 'google' ? settings.googleStatus() : settings.appleStatus()
})

const statusClass = computed(() => status.value)
const statusLabel = computed(() => {
  const map = { ok: '已連線', pending: '待設定', none: '未啟用' }
  return map[status.value] || '未啟用'
})
</script>

<style scoped>
.plat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.plat-info {
  display: flex;
  align-items: center;
  gap: 12px;
}
.plat-logo {
  font-size: 28px;
}
.plat-name {
  font-size: 15px;
  font-weight: 800;
}
.plat-desc {
  font-size: 12px;
  color: var(--gray-mid);
}
.plat-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.plat-status {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 6px;
}
.plat-status.ok {
  background: var(--teal-light);
  color: var(--teal);
}
.plat-status.pending {
  background: var(--gold-pale);
  color: var(--gold);
}
.plat-status.none {
  background: var(--gray-pale);
  color: var(--gray-mid);
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
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
.plat-actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}
.divider {
  border: none;
  border-top: 1.5px solid var(--gray-light);
  margin: 16px 0;
}

@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
