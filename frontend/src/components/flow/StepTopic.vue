<template>
  <div class="step-topic anim-rise">
    <div class="step-icon anim-bobble">📝</div>
    <h1 class="step-h1">這集要聊什麼？</h1>

    <textarea
      class="inp topic-inp"
      placeholder="輸入這集的主題或大綱，例如：分享 5 個我每天用的 AI 工具..."
      :value="flow.topic"
      @input="flow.topic = $event.target.value"
      maxlength="200"
      rows="4"
    ></textarea>
    <div class="char-count">{{ flow.topic.length }} / 200</div>

    <div class="card">
      <div class="card-label">👥 目標聽眾（可多選）</div>
      <div class="opt-grid">
        <OptionButton
          v-for="a in audienceOptions"
          :key="a.label"
          :icon="a.icon"
          :label="a.label"
          :selected="flow.audience.includes(a.label)"
          @select="toggleAudience(a.label)"
        />
      </div>
    </div>

    <div class="card">
      <div class="card-label">⏱ 節目長度</div>
      <div class="opt-grid">
        <OptionButton
          v-for="d in durationOptions"
          :key="d.label"
          :icon="d.icon"
          :label="d.label"
          :sublabel="d.sub"
          :selected="flow.duration === d.label"
          @select="flow.duration = d.label"
        />
      </div>
    </div>

    <div class="card">
      <div class="card-label">🎨 節目風格</div>
      <div class="opt-grid">
        <OptionButton
          v-for="s in styleOptions"
          :key="s.label"
          :icon="s.icon"
          :label="s.label"
          :selected="flow.style === s.label"
          @select="flow.style = s.label"
        />
      </div>
    </div>

    <div class="card">
      <div class="card-label">🎤 主持人數</div>
      <div class="opt-grid">
        <OptionButton
          v-for="h in hostOptions"
          :key="h.label"
          :icon="h.icon"
          :label="h.label"
          :selected="flow.hostCount === h.label"
          @select="flow.hostCount = h.label"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { useFlowStore } from '../../stores/flow'
import OptionButton from './OptionButton.vue'

const flow = useFlowStore()

const audienceOptions = [
  { icon: '🧑‍💻', label: '科技人' },
  { icon: '🎓', label: '學生' },
  { icon: '💼', label: '上班族' },
  { icon: '🌍', label: '一般大眾' },
  { icon: '🎨', label: '創作者' },
  { icon: '📈', label: '創業者' },
]

const durationOptions = [
  { icon: '⚡', label: '15 分鐘', sub: '短講' },
  { icon: '☕', label: '30 分鐘', sub: '標準' },
  { icon: '🎧', label: '60 分鐘', sub: '深度' },
]

const styleOptions = [
  { icon: '💬', label: '輕鬆聊天' },
  { icon: '📚', label: '知識分享' },
  { icon: '🎯', label: '深度分析' },
  { icon: '😂', label: '幽默搞笑' },
  { icon: '📰', label: '新聞評論' },
  { icon: '🎤', label: '訪談對話' },
]

const hostOptions = [
  { icon: '🧍', label: '我一人' },
  { icon: '👥', label: '雙人對談' },
  { icon: '👥👤', label: '三人以上' },
]

function toggleAudience(label) {
  const idx = flow.audience.indexOf(label)
  if (idx >= 0) {
    flow.audience.splice(idx, 1)
  } else {
    flow.audience.push(label)
  }
}
</script>

<style scoped>
.step-topic {
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
.topic-inp {
  min-height: 100px;
  margin-bottom: 0;
}
.card {
  text-align: left;
}
</style>
