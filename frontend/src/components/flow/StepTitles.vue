<template>
  <div class="step-titles anim-rise">
    <div class="step-icon anim-bobble">✨</div>
    <h1 class="step-h1">選一個你最喜歡的標題</h1>

    <div class="title-list">
      <TitleCard
        v-for="(t, i) in flow.titles"
        :key="i"
        :title="t"
        :index="i"
        :selected="flow.selectedTitleIndex === i"
        @select="flow.selectTitle(i)"
      />
    </div>

    <button class="btn-secondary regen-btn" @click="flow.regenerateTitles()">
      🔄 換 5 個新標題
    </button>
  </div>
</template>

<script setup>
import { useFlowStore } from '../../stores/flow'
import TitleCard from './TitleCard.vue'

const flow = useFlowStore()
</script>

<style scoped>
.step-titles {
  text-align: center;
}
.step-icon {
  font-size: 56px;
  margin-bottom: 10px;
}
.step-h1 {
  font-family: var(--font-display);
  font-size: 30px;
  font-weight: 700;
  margin-bottom: 22px;
}
.title-list {
  display: flex;
  flex-direction: column;
  gap: 11px;
  margin-bottom: 18px;
}
.regen-btn {
  margin: 0 auto;
}
</style>
