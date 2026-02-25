<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-backdrop" @click.self="handleClose">
      <div class="pub-modal anim-pop">
        <!-- Step 1: Config -->
        <template v-if="step === 1">
          <h3 class="pm-title">📡 發佈到 Podcast 平台</h3>
          <p class="pm-sub">選擇平台並填寫發佈資訊</p>

          <div class="card-label">平台</div>
          <div class="plat-row">
            <button
              class="plat-btn"
              :class="{ sel: platform === 'google' }"
              @click="platform = 'google'"
            >🟢 Google Podcasts</button>
            <button
              class="plat-btn"
              :class="{ sel: platform === 'apple' }"
              @click="platform = 'apple'"
            >🍎 Apple Podcasts</button>
          </div>

          <div class="pm-form">
            <label class="pm-field">
              <span>集數標題</span>
              <input class="inp" v-model="form.title" />
            </label>
            <label class="pm-field">
              <span>摘要</span>
              <textarea class="inp" v-model="form.summary" rows="3"></textarea>
            </label>
            <div class="pm-row">
              <label class="pm-field">
                <span>第幾集</span>
                <input class="inp" v-model="form.episodeNum" type="number" min="1" />
              </label>
              <label class="pm-field">
                <span>發佈日期</span>
                <input class="inp" v-model="form.date" type="date" />
              </label>
            </div>
            <label class="pm-field">
              <span>音檔 URL</span>
              <input class="inp" v-model="form.audioUrl" placeholder="https://..." />
            </label>
          </div>

          <div class="tip-box">
            <span>⚠️</span>
            <span>請確認音檔已上傳至可公開存取的位置。</span>
          </div>

          <div class="pm-actions">
            <button class="btn-secondary" @click="handleClose">取消</button>
            <button class="btn-primary pm-pub" @click="startPublish">發佈</button>
          </div>
        </template>

        <!-- Step 2: Publishing -->
        <template v-if="step === 2">
          <div class="pm-loading">
            <div class="spin"></div>
            <h3>發佈中...</h3>
            <p>正在上傳到 {{ platform === 'google' ? 'Google' : 'Apple' }} Podcasts</p>
          </div>
        </template>

        <!-- Step 3: Success -->
        <template v-if="step === 3">
          <div class="pm-success">
            <div class="success-circle">🎊</div>
            <h3>發佈成功！</h3>
            <p>你的節目已送出審核，通常 24-48 小時內會上架。</p>
            <button class="btn-primary" @click="handleClose">完成</button>
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  episodeTitle: { type: String, default: '' },
})

const emit = defineEmits(['close'])

const step = ref(1)
const platform = ref('google')
const form = reactive({
  title: '',
  summary: '',
  episodeNum: 1,
  date: new Date().toISOString().slice(0, 10),
  audioUrl: '',
})

watch(() => props.visible, (v) => {
  if (v) {
    step.value = 1
    form.title = props.episodeTitle
  }
})

function startPublish() {
  step.value = 2
  setTimeout(() => {
    step.value = 3
  }, 2500)
}

function handleClose() {
  emit('close')
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.4);
  z-index: 150;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.pub-modal {
  background: var(--warm-white);
  border-radius: var(--radius);
  padding: 28px;
  width: 100%;
  max-width: 500px;
  max-height: 85vh;
  overflow-y: auto;
}
.pm-title {
  font-size: 20px;
  font-weight: 800;
  margin-bottom: 4px;
}
.pm-sub {
  font-size: 14px;
  color: var(--gray-mid);
  margin-bottom: 18px;
}
.card-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--gray-mid);
  margin-bottom: 8px;
}
.plat-row {
  display: flex;
  gap: 9px;
  margin-bottom: 16px;
}
.plat-btn {
  flex: 1;
  padding: 12px;
  border: 2px solid var(--gray-light);
  border-radius: var(--radius-sm);
  background: #fff;
  font-size: 13px;
  font-weight: 700;
  font-family: var(--font-body);
  cursor: pointer;
  transition: all .15s;
}
.plat-btn:hover {
  border-color: var(--orange);
}
.plat-btn.sel {
  border-color: var(--orange);
  background: var(--orange-pale);
  color: var(--orange);
}
.pm-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 14px;
}
.pm-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}
.pm-field span {
  font-size: 12px;
  font-weight: 700;
  color: var(--gray-mid);
}
.pm-row {
  display: flex;
  gap: 12px;
}
.pm-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 14px;
}
.pm-pub {
  width: auto;
  padding: 12px 28px;
}
.pm-loading, .pm-success {
  text-align: center;
  padding: 40px 20px;
}
.pm-loading h3, .pm-success h3 {
  font-size: 20px;
  font-weight: 800;
  margin: 16px 0 6px;
}
.pm-loading p, .pm-success p {
  font-size: 14px;
  color: var(--gray-mid);
}
.spin {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 4px solid var(--orange-pale);
  border-top-color: var(--orange);
  animation: spin .8s linear infinite;
  margin: 0 auto;
}
@keyframes spin { to { transform: rotate(360deg); } }
.pm-success .btn-primary {
  margin-top: 20px;
  width: auto;
  padding: 12px 32px;
  display: inline-flex;
}
</style>
