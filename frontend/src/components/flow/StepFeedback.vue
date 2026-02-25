<template>
  <div class="step-feedback anim-rise">
    <div class="step-icon anim-bobble">⭐</div>
    <h1 class="step-h1">這個腳本好用嗎？</h1>

    <div class="card">
      <div class="card-label">📊 評分</div>
      <StarRating label="自然程度" v-model="flow.ratings.naturalness" />
      <StarRating label="節奏安排" v-model="flow.ratings.pacing" />
      <StarRating label="風格符合" v-model="flow.ratings.style" />
    </div>

    <div class="card">
      <div class="card-label">💬 你的意見</div>
      <textarea
        class="inp"
        placeholder="哪裡可以改進？例如：開場太長、某段的比喻不夠生動..."
        v-model="flow.feedbackText"
        rows="4"
      ></textarea>
      <div class="quick-tags">
        <button
          v-for="tag in quickTags"
          :key="tag"
          class="qtag"
          @click="appendTag(tag)"
        >{{ tag }}</button>
      </div>
    </div>

    <button class="btn-primary" @click="flow.submitFeedback()">
      🔄 重新優化腳本
    </button>
    <button class="btn-secondary done-btn" @click="$emit('satisfied')">
      滿意了，去下載腳本 →
    </button>
  </div>
</template>

<script setup>
import { useFlowStore } from '../../stores/flow'
import StarRating from './StarRating.vue'

const flow = useFlowStore()

defineEmits(['satisfied'])

const quickTags = [
  '開場太長',
  '語氣太正式',
  '需要更多案例',
  '結尾不夠有力',
  '節奏太趕',
  '可以更有趣',
]

function appendTag(tag) {
  if (flow.feedbackText) {
    flow.feedbackText += '；' + tag
  } else {
    flow.feedbackText = tag
  }
}
</script>

<style scoped>
.step-feedback {
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
.card {
  text-align: left;
}
.quick-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 10px;
}
.qtag {
  padding: 5px 12px;
  border: 1.5px solid var(--gray-light);
  border-radius: 99px;
  background: var(--warm-white);
  font-size: 12px;
  font-weight: 600;
  font-family: var(--font-body);
  color: var(--gray-mid);
  cursor: pointer;
  transition: all .15s;
}
.qtag:hover {
  border-color: var(--orange);
  color: var(--orange);
  background: var(--orange-pale);
}
.btn-primary {
  margin-top: 8px;
}
.done-btn {
  margin: 14px auto 0;
  display: block;
}
</style>
