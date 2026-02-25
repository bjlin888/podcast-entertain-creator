<template>
  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-icon si-total">📊</div>
      <div class="stat-num">{{ total }}</div>
      <div class="stat-label">全部集數</div>
    </div>
    <div class="stat-card">
      <div class="stat-icon si-done">✅</div>
      <div class="stat-num">{{ done }}</div>
      <div class="stat-label">已完成</div>
    </div>
    <div class="stat-card">
      <div class="stat-icon si-draft">✏️</div>
      <div class="stat-num">{{ draft }}</div>
      <div class="stat-label">進行中</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  total: { type: Number, default: 0 },
  done: { type: Number, default: 0 },
  draft: { type: Number, default: 0 },
})
</script>

<style scoped>
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 28px;
}
.stat-card {
  background: var(--warm-white);
  border-radius: var(--radius);
  padding: 20px;
  text-align: center;
  border: 1.5px solid var(--gray-light);
  box-shadow: var(--shadow-card);
  transition: transform .2s;
}
.stat-card:hover {
  transform: translateY(-3px);
}
.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  margin: 0 auto 10px;
}
.si-total { background: var(--orange-pale); }
.si-done { background: var(--teal-light); }
.si-draft { background: var(--gold-pale); }
.stat-num {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 700;
  color: var(--ink);
  line-height: 1;
  margin-bottom: 4px;
}
.stat-label {
  font-size: 12px;
  color: var(--gray-mid);
  font-weight: 600;
}

@media (max-width: 640px) {
  .stats-row {
    gap: 9px;
  }
  .stat-card {
    padding: 14px 10px;
  }
  .stat-num {
    font-size: 24px;
  }
}
</style>
