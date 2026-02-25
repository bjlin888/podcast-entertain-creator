<template>
  <Teleport to="body">
    <div v-if="visible" class="loading-overlay">
      <div class="spin"></div>
      <div class="load-txt">{{ text }}</div>
      <div class="load-sub">{{ subText }}</div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  text: { type: String, default: 'AI 正在思考中...' },
  subText: { type: String, default: '通常需要 10-30 秒，請稍候' },
})
</script>

<style scoped>
.loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(253,246,236,.93);
  z-index: 200;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18px;
  backdrop-filter: blur(4px);
}

.spin {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  border: 4px solid var(--orange-pale);
  border-top-color: var(--orange);
  animation: spin .8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.load-txt {
  font-size: 17px;
  font-weight: 700;
}

.load-sub {
  font-size: 13px;
  color: var(--gray-mid);
}
</style>
