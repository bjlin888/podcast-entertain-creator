<template>
  <div class="seg-card" :class="{ open: isOpen }">
    <div class="seg-header" @click="$emit('toggle')">
      <span class="seg-tag" :class="segment.tag || 'seg'">
        {{ tagLabel }}
      </span>
      <span class="seg-name">{{ segment.label || segment.id }}</span>
      <span class="seg-dur">{{ segment.dur || '' }}</span>
      <span class="seg-arrow">{{ isOpen ? '▲' : '▼' }}</span>
    </div>

    <div v-if="isOpen" class="seg-body">
      <pre class="seg-content">{{ segment.content }}</pre>

      <div v-if="segment.cues && segment.cues.length" class="seg-cues">
        <span v-for="(cue, ci) in segment.cues" :key="ci" class="cue-badge">{{ cue }}</span>
      </div>

      <div class="seg-actions">
        <button class="btn-sm bsm-edit" @click="$emit('edit', index)">✏️ 修改</button>
        <button class="btn-sm bsm-audio" @click="$emit('voice', index)">🎧 試聽</button>
      </div>

      <!-- Audio player if available -->
      <div v-if="segment.audioUrl" class="audio-player">
        <audio ref="audioEl" :src="segment.audioUrl" preload="metadata"
          @timeupdate="onTimeUpdate" @ended="playing = false" />
        <button class="audio-play-btn" @click="togglePlay">
          {{ playing ? '⏸' : '▶' }}
        </button>
        <div class="audio-info">
          <div class="audio-lbl">示範音檔</div>
          <div class="audio-track">
            <div class="audio-prog" :style="{ width: audioProgress + '%' }"></div>
          </div>
        </div>
      </div>

      <!-- Host audio upload -->
      <div class="seg-upload">
        <label class="upload-label">
          <input type="file" accept="audio/*" class="upload-inp" @change="handleUpload" />
          📎 上傳你的錄音
        </label>
        <span v-if="segment.hostAudioUrl" class="upload-done">✅ 已上傳</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  segment: { type: Object, required: true },
  index: { type: Number, default: 0 },
  isOpen: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle', 'edit', 'voice', 'play', 'upload'])

const TAG_LABELS = {
  'cold-open': '冷開場', jingle: '品牌 Jingle', 'host-intro': '主持人介紹',
  'topic-intro': '主題引入', core: '核心內容', 'ad-break': '廣告/互動',
  summary: '重點摘要', cta: '行動呼籲', preview: '下集預告',
  // Legacy
  intro: '開場白', seg: '內容段', outro: '結尾',
}

const tagLabel = computed(() => props.segment.label || TAG_LABELS[props.segment.tag] || '段落')

const audioEl = ref(null)
const playing = ref(false)
const audioProgress = ref(0)

function togglePlay() {
  const el = audioEl.value
  if (!el) return
  if (playing.value) {
    el.pause()
    playing.value = false
  } else {
    el.play()
    playing.value = true
  }
}

function onTimeUpdate() {
  const el = audioEl.value
  if (el && el.duration) {
    audioProgress.value = (el.currentTime / el.duration) * 100
  }
}

function handleUpload(e) {
  const file = e.target.files?.[0]
  if (file) {
    emit('upload', { index: props.index, file })
  }
}
</script>

<style scoped>
.seg-card {
  background: var(--warm-white);
  border: 1.5px solid var(--gray-light);
  border-radius: var(--radius-sm);
  overflow: hidden;
  transition: border-color .2s;
}
.seg-card.open {
  border-color: var(--orange);
}
.seg-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  cursor: pointer;
  transition: background .15s;
}
.seg-header:hover {
  background: var(--gray-pale);
}
.seg-tag {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 6px;
}
/* Gold: cold-open, jingle */
.seg-tag.cold-open,
.seg-tag.jingle {
  background: var(--gold-pale);
  color: var(--gold);
}
/* Teal: host-intro, topic-intro */
.seg-tag.host-intro,
.seg-tag.topic-intro {
  background: var(--teal-light);
  color: var(--teal);
}
/* Blue: core */
.seg-tag.core {
  background: var(--blue-pale);
  color: var(--blue);
}
/* Purple: ad-break, summary */
.seg-tag.ad-break,
.seg-tag.summary {
  background: var(--purple-pale);
  color: var(--purple);
}
/* Orange: cta, preview */
.seg-tag.cta,
.seg-tag.preview {
  background: var(--orange-pale);
  color: var(--orange);
}
/* Legacy classes */
.seg-tag.intro {
  background: var(--gold-pale);
  color: var(--gold);
}
.seg-tag.seg {
  background: var(--teal-light);
  color: var(--teal);
}
.seg-tag.outro {
  background: var(--orange-pale);
  color: var(--orange);
}
.seg-name {
  flex: 1;
  font-size: 14px;
  font-weight: 700;
}
.seg-dur {
  font-size: 12px;
  color: var(--gray-mid);
}
.seg-arrow {
  font-size: 11px;
  color: var(--gray-mid);
}
.seg-body {
  padding: 0 16px 16px;
  animation: riseIn .2s ease;
}
.seg-content {
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: var(--ink);
  margin-bottom: 12px;
}
.seg-cues {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 12px;
}
.seg-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.audio-player {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--gray-pale);
  border-radius: var(--radius-sm);
  margin-bottom: 12px;
}
.audio-player audio {
  display: none;
}
.audio-play-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--orange);
  color: #fff;
  font-size: 16px;
  cursor: pointer;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.audio-info {
  flex: 1;
  min-width: 0;
}
.audio-lbl {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 4px;
}
.audio-track {
  height: 4px;
  background: var(--gray-light);
  border-radius: 2px;
  overflow: hidden;
}
.audio-prog {
  height: 100%;
  background: var(--orange);
  border-radius: 2px;
  transition: width .15s;
}
.seg-upload {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}
.upload-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--teal);
  cursor: pointer;
  transition: opacity .15s;
}
.upload-label:hover {
  opacity: .7;
}
.upload-inp {
  display: none;
}
.upload-done {
  font-size: 12px;
  color: var(--teal);
  font-weight: 600;
}
</style>
