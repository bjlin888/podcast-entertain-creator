<template>
  <div class="ep-card" @click="$emit('open', episode)">
    <div class="ep-cover" :style="{ background: cover.grad }">
      <span class="ep-emoji">{{ cover.emoji }}</span>
      <span class="ep-badge">EP{{ displayIndex }}</span>
      <div class="ep-dot" :class="episode.status"></div>
      <div class="ep-quick">
        <button class="qb" @click.stop="$emit('continue', episode)" title="繼續編輯">▶</button>
        <button class="qb qb-del" @click.stop="$emit('delete', episode)" title="刪除">🗑</button>
      </div>
    </div>
    <div class="ep-body">
      <span class="ep-status" :class="episode.status">
        {{ episode.status === 'done' ? '已完成' : stepLabel }}
      </span>
      <h3 class="ep-title">{{ episode.title }}</h3>
      <div class="ep-tags">
        <span v-if="episode.style" class="ep-tag">{{ episode.style }}</span>
        <span v-if="episode.dur" class="ep-tag">{{ episode.dur }}</span>
      </div>
      <div class="ep-prog-wrap">
        <div class="ep-prog-bar">
          <div class="ep-prog-fill" :style="{ width: episode.progress + '%' }"></div>
        </div>
        <span class="ep-prog-pct">{{ episode.progress }}%</span>
      </div>
      <div class="ep-actions">
        <button class="btn-sm bsm-edit" @click.stop="$emit('continue', episode)">
          {{ episode.status === 'done' ? '查看' : '繼續' }}
        </button>
        <button
          v-if="episode.status === 'done'"
          class="btn-sm bsm-audio"
          @click.stop="$emit('publish', episode)"
        >發佈</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { COVERS, STEP_LABELS } from '../../stores/episodes'

const props = defineProps({
  episode: { type: Object, required: true },
  index: { type: Number, default: 0 },
})

defineEmits(['open', 'continue', 'delete', 'publish'])

const cover = computed(() => COVERS[props.episode.ci % COVERS.length])
const displayIndex = computed(() => props.index + 1)
const stepLabel = computed(() => STEP_LABELS[props.episode.step] || '草稿')
</script>

<style scoped>
.ep-card {
  background: var(--warm-white);
  border-radius: var(--radius);
  border: 1.5px solid var(--gray-light);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  cursor: pointer;
  transition: all .22s;
}
.ep-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 8px 32px rgba(0,0,0,.12);
  border-color: rgba(244,99,30,.3);
}
.ep-cover {
  height: 118px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.ep-emoji {
  font-size: 44px;
  opacity: .7;
}
.ep-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(0,0,0,.35);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  backdrop-filter: blur(4px);
}
.ep-dot {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.ep-dot.done {
  background: var(--teal);
  box-shadow: 0 0 0 3px rgba(26,143,138,.25);
}
.ep-dot.draft {
  background: var(--orange);
  animation: dotpulse 2s ease infinite;
}
.ep-quick {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,.45);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  opacity: 0;
  transition: opacity .2s;
}
.ep-card:hover .ep-quick {
  opacity: 1;
}
.qb {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255,255,255,.92);
  border: none;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform .15s;
}
.qb:hover {
  transform: scale(1.1);
}
.qb-del:hover {
  background: #FEE;
}
.ep-body {
  padding: 14px 16px 16px;
}
.ep-status {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 6px;
  display: inline-block;
  margin-bottom: 8px;
}
.ep-status.done {
  background: var(--teal-light);
  color: var(--teal);
}
.ep-status.draft {
  background: var(--orange-pale);
  color: var(--orange);
}
.ep-title {
  font-size: 15px;
  font-weight: 800;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8px;
}
.ep-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.ep-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 5px;
  background: var(--gray-pale);
  color: var(--gray-mid);
  font-weight: 600;
}
.ep-prog-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.ep-prog-bar {
  flex: 1;
  height: 5px;
  background: var(--gray-pale);
  border-radius: 99px;
  overflow: hidden;
}
.ep-prog-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--orange), #FF8A50);
  border-radius: 99px;
  transition: width .3s;
}
.ep-prog-pct {
  font-size: 11px;
  font-weight: 700;
  color: var(--gray-mid);
  min-width: 32px;
  text-align: right;
}
.ep-actions {
  display: flex;
  gap: 8px;
}
</style>
