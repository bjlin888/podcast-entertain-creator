<template>
  <div class="flow-progress">
    <div class="flow-progress-fill" :style="{ width: percent + '%' }"></div>
  </div>
</template>

<script setup>
defineProps({
  percent: { type: Number, default: 0 },
})
</script>

<style scoped>
.flow-progress {
  height: 7px;
  background: var(--gray-pale);
  border-radius: 99px;
  overflow: hidden;
  margin-bottom: 28px;
}
.flow-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--orange), #FF8A50);
  border-radius: 99px;
  transition: width .4s cubic-bezier(.4,0,.2,1);
}
</style>
