<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-backdrop" @click.self="$emit('close')">
      <div class="voice-sheet anim-slide-up">
        <div class="sheet-handle"></div>
        <h2 class="sheet-title">🎧 設定示範聲音</h2>

        <div class="card-label">TTS 引擎</div>
        <div class="opt-grid">
          <button
            class="opt-btn"
            :class="{ sel: config.ttsProvider === 'gemini' }"
            @click="config.ttsProvider = 'gemini'"
          >
            <span class="oi">✨</span>
            <span>Gemini AI 語音</span>
          </button>
          <button
            class="opt-btn"
            :class="{ sel: config.ttsProvider === 'google' }"
            @click="config.ttsProvider = 'google'"
          >
            <span class="oi">🔊</span>
            <span>Cloud TTS</span>
          </button>
        </div>

        <!-- Multi-speaker mode for 2+ hosts -->
        <template v-if="isMultiSpeaker && config.ttsProvider === 'gemini'">
          <div class="card-label">多人對話模式</div>
          <div class="multi-speaker-config">
            <div class="speaker-row">
              <span class="speaker-label">主持人A</span>
              <div class="opt-grid speaker-grid">
                <button
                  v-for="v in geminiVoices"
                  :key="'a-' + v.value"
                  class="opt-btn"
                  :class="{ sel: config.speakers[0].voice === v.value }"
                  @click="config.speakers[0].voice = v.value"
                >
                  <span class="oi">{{ v.icon }}</span>
                  <span>{{ v.label }}</span>
                </button>
              </div>
            </div>
            <div class="speaker-row">
              <span class="speaker-label">主持人B</span>
              <div class="opt-grid speaker-grid">
                <button
                  v-for="v in geminiVoices"
                  :key="'b-' + v.value"
                  class="opt-btn"
                  :class="{ sel: config.speakers[1].voice === v.value }"
                  @click="config.speakers[1].voice = v.value"
                >
                  <span class="oi">{{ v.icon }}</span>
                  <span>{{ v.label }}</span>
                </button>
              </div>
            </div>
          </div>
        </template>

        <!-- Single speaker voice selection -->
        <template v-else>
          <div class="card-label">聲音</div>
          <div class="opt-grid">
            <button
              v-for="v in voices"
              :key="v.value"
              class="opt-btn"
              :class="{ sel: config.voice === v.value }"
              @click="config.voice = v.value"
            >
              <span class="oi">{{ v.icon }}</span>
              <span>{{ v.label }}</span>
            </button>
          </div>
        </template>

        <template v-if="config.ttsProvider === 'gemini'">
          <div class="card-label">語音風格</div>
          <div class="opt-grid">
            <button
              v-for="s in stylePresets"
              :key="s.value"
              class="opt-btn"
              :class="{ sel: config.stylePrompt === s.value }"
              @click="config.stylePrompt = s.value"
            >
              <span class="oi">{{ s.icon }}</span>
              <span>{{ s.label }}</span>
            </button>
          </div>
        </template>

        <template v-if="config.ttsProvider === 'google'">
          <div class="card-label">速度</div>
          <div class="opt-grid">
            <button
              v-for="s in speeds"
              :key="s.value"
              class="opt-btn"
              :class="{ sel: config.speed === s.value }"
              @click="config.speed = s.value"
            >
              <span class="oi">{{ s.icon }}</span>
              <span>{{ s.label }}</span>
            </button>
          </div>

          <div class="card-label">音調</div>
          <div class="opt-grid">
            <button
              v-for="p in pitches"
              :key="p.value"
              class="opt-btn"
              :class="{ sel: config.pitch === p.value }"
              @click="config.pitch = p.value"
            >
              <span class="oi">{{ p.icon }}</span>
              <span>{{ p.label }}</span>
            </button>
          </div>
        </template>

        <button
          v-if="isMultiSpeaker && config.ttsProvider === 'gemini'"
          class="btn-primary gen-btn"
          @click="handleGenerateMulti"
        >
          🎙️ 整集試聽（多人對話）
        </button>
        <button v-else class="btn-primary gen-btn" @click="handleGenerate">
          🔊 開始生成示範音檔
        </button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { reactive, computed } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  segmentIndex: { type: Number, default: 0 },
  hostCount: { type: Number, default: 1 },
})

const emit = defineEmits(['close', 'generate', 'generate-multi'])

const isMultiSpeaker = computed(() => props.hostCount >= 2)

const config = reactive({
  voice: 'female',
  speed: 'normal',
  pitch: 'normal',
  ttsProvider: 'gemini',
  stylePrompt: '',
  speakers: [
    { name: '主持人A', voice: 'Achird' },
    { name: '主持人B', voice: 'Kore' },
  ],
})

const voices = [
  { value: 'female', icon: '👩', label: '女聲' },
  { value: 'male', icon: '👨', label: '男聲' },
]
const geminiVoices = [
  { value: 'Achird', icon: '👨', label: '男聲 (Achird)' },
  { value: 'Kore', icon: '👩', label: '女聲 (Kore)' },
  { value: 'Charon', icon: '🧔', label: '男聲 (Charon)' },
  { value: 'Fenrir', icon: '👩‍🦰', label: '女聲 (Fenrir)' },
]
const speeds = [
  { value: 'slow', icon: '🐢', label: '慢速' },
  { value: 'normal', icon: '🏃', label: '正常' },
  { value: 'fast', icon: '⚡', label: '快速' },
]
const pitches = [
  { value: 'low', icon: '🔉', label: '低音' },
  { value: 'normal', icon: '🔊', label: '正常' },
  { value: 'high', icon: '🔔', label: '高音' },
]
const stylePresets = [
  { value: '', icon: '🎙️', label: '自然' },
  { value: '用輕鬆閒聊的語氣，像朋友之間的對話', icon: '☕', label: '輕鬆聊天' },
  { value: '用專業知識分享的語氣，清晰有條理', icon: '📚', label: '專業知識' },
  { value: '用熱情有活力的語氣，充滿感染力', icon: '🔥', label: '熱情活力' },
]

function handleGenerate() {
  emit('generate', {
    segmentIndex: props.segmentIndex,
    ...config,
  })
}

function handleGenerateMulti() {
  emit('generate-multi', {
    speakers: config.speakers.map(s => ({ ...s })),
    stylePrompt: config.stylePrompt,
    ttsProvider: config.ttsProvider,
  })
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.4);
  z-index: 150;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.voice-sheet {
  background: var(--warm-white);
  border-radius: 26px 26px 0 0;
  padding: 20px 24px 32px;
  width: 100%;
  max-width: 480px;
  max-height: 85vh;
  overflow-y: auto;
}
.sheet-handle {
  width: 40px;
  height: 4px;
  background: var(--gray-light);
  border-radius: 2px;
  margin: 0 auto 16px;
}
.sheet-title {
  font-size: 18px;
  font-weight: 800;
  text-align: center;
  margin-bottom: 18px;
}
.card-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--gray-mid);
  margin: 14px 0 8px;
}
.opt-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 9px;
}
.gen-btn {
  margin-top: 20px;
}
.multi-speaker-config {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.speaker-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.speaker-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--gray-dark, #333);
}
.speaker-grid {
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
}
</style>
