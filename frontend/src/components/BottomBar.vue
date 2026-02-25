<template>
  <div v-if="visible" class="bot-bar">
    <button class="bot-back" @click="$emit('back')">← 上一步</button>
    <button
      class="bot-next"
      :disabled="!canProceed"
      @click="$emit('next')"
    >
      <span>{{ nextLabel }}</span> ➜
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentStep: { type: Number, default: 1 },
  canProceed: { type: Boolean, default: true },
})

defineEmits(['back', 'next'])

const visible = computed(() => {
  return props.currentStep >= 1 && props.currentStep <= 3
})

const nextLabel = computed(() => {
  if (props.currentStep === 3) return '腳本看完了，繼續'
  return '下一步'
})
</script>

<style scoped>
.bot-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--warm-white);
  border-top: 2px solid var(--gray-light);
  padding: 12px 22px;
  display: flex;
  gap: 11px;
  align-items: center;
  box-shadow: 0 -4px 24px rgba(0,0,0,.06);
  z-index: 99;
}

.bot-back {
  padding: 13px 18px;
  background: var(--gray-pale);
  color: var(--ink);
  border: 2px solid var(--gray-light);
  border-radius: var(--radius-sm);
  font-size: 15px;
  font-weight: 700;
  font-family: var(--font-body);
  cursor: pointer;
  white-space: nowrap;
  transition: all .18s;
}
.bot-back:hover {
  background: var(--gray-light);
}

.bot-next {
  flex: 1;
  padding: 15px 22px;
  background: var(--orange);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 16px;
  font-weight: 700;
  font-family: var(--font-body);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  transition: all .2s;
}
.bot-next:hover {
  background: #FF7A3A;
  box-shadow: 0 4px 16px rgba(244,99,30,.35);
}
.bot-next:disabled {
  background: var(--gray-light);
  color: var(--gray-mid);
  cursor: not-allowed;
  box-shadow: none;
}
</style>
