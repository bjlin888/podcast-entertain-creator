<template>
  <nav class="topbar" :class="mode">
    <router-link to="/" class="logo">
      <div class="logo-icon">🎙️</div>
      Podcast 創作助手
    </router-link>

    <div class="topbar-right">
      <!-- Flow navigation dots (only in flow mode) -->
      <div v-if="isFlow" class="flow-nav-wrap">
        <div class="flow-nav">
          <template v-for="step in 5" :key="step">
            <div
              class="flow-dot"
              :class="{
                active: step === currentStep,
                done: step < currentStep,
              }"
            >{{ step }}</div>
            <div
              v-if="step < 5"
              class="flow-line"
              :class="{ done: step < currentStep }"
            ></div>
          </template>
        </div>
        <button class="btn-to-dash" @click="$router.push('/')">← 我的集數</button>
      </div>

      <!-- Settings button -->
      <button
        class="btn-settings"
        :class="{ active: isSettings }"
        @click="toggleSettings"
        title="系統設定"
      >⚙️</button>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useFlowStore } from '../stores/flow'

const route = useRoute()
const router = useRouter()
const flowStore = useFlowStore()

const isFlow = computed(() => route.name === 'flow')
const isSettings = computed(() => route.name === 'settings')
const isDark = computed(() => !isFlow.value)
const mode = computed(() => isFlow.value ? 'light' : 'dark')
const currentStep = computed(() => flowStore.currentStep)

function toggleSettings() {
  if (isSettings.value) {
    router.push('/')
  } else {
    router.push('/settings')
  }
}
</script>

<style scoped>
.topbar {
  height: 62px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  position: sticky;
  top: 0;
  z-index: 120;
  transition: background .3s;
}
.topbar.dark {
  background: var(--ink-soft);
  border-bottom: 1px solid rgba(255,255,255,.07);
}
.topbar.light {
  background: var(--warm-white);
  border-bottom: 2px solid var(--gray-light);
  box-shadow: 0 2px 12px rgba(0,0,0,.04);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 900;
  font-size: 18px;
  cursor: pointer;
  text-decoration: none;
  transition: opacity .15s;
}
.logo:hover {
  opacity: .8;
}
.topbar.dark .logo {
  color: #fff;
}
.topbar.light .logo {
  color: var(--ink);
}

.logo-icon {
  width: 34px;
  height: 34px;
  background: var(--orange);
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  flex-shrink: 0;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.flow-nav-wrap {
  display: flex;
  align-items: center;
  gap: 14px;
}

.flow-nav {
  display: flex;
  align-items: center;
  gap: 5px;
}
.flow-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid var(--gray-light);
  background: transparent;
  color: var(--gray-mid);
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .2s;
}
.flow-dot.active {
  border-color: var(--orange);
  background: var(--orange);
  color: #fff;
}
.flow-dot.done {
  border-color: var(--teal);
  background: var(--teal);
  color: #fff;
}
.flow-line {
  width: 18px;
  height: 2px;
  background: var(--gray-light);
  border-radius: 2px;
}
.flow-line.done {
  background: var(--teal);
}

.btn-to-dash {
  padding: 7px 14px;
  background: var(--gray-pale);
  border: 1.5px solid var(--gray-light);
  border-radius: var(--radius-xs);
  font-size: 12px;
  font-weight: 700;
  font-family: var(--font-body);
  color: var(--gray-mid);
  cursor: pointer;
  transition: all .15s;
  white-space: nowrap;
}
.btn-to-dash:hover {
  background: var(--gray-light);
  color: var(--ink);
}

.btn-settings {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  background: rgba(255,255,255,.1);
  border: 1.5px solid rgba(255,255,255,.14);
  color: rgba(255,255,255,.7);
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .18s;
}
.btn-settings:hover {
  background: rgba(255,255,255,.18);
  color: #fff;
}
.btn-settings.active {
  background: var(--teal) !important;
  border-color: var(--teal) !important;
  color: #fff !important;
}
.topbar.light .btn-settings {
  background: var(--gray-pale);
  border-color: var(--gray-light);
  color: var(--gray-mid);
}
.topbar.light .btn-settings:hover {
  background: var(--gray-light);
  color: var(--ink);
}

@media (max-width: 640px) {
  .topbar {
    padding: 0 14px;
  }
  .flow-nav {
    display: none;
  }
}
</style>
