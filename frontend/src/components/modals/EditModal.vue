<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-backdrop" @click.self="$emit('close')">
      <div class="edit-modal anim-pop">
        <div class="em-header">
          <h3>✏️ 編輯段落</h3>
          <button class="em-close" @click="$emit('close')">✕</button>
        </div>
        <div class="em-label">{{ segmentLabel }}</div>
        <textarea
          class="inp em-textarea"
          v-model="localContent"
          rows="10"
        ></textarea>
        <p class="em-hint">修改後可再按「試聽」重新生成語音。</p>
        <div class="em-actions">
          <button class="btn-secondary" @click="$emit('close')">取消</button>
          <button class="btn-primary em-save" @click="handleSave">確認修改</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  segmentLabel: { type: String, default: '' },
  content: { type: String, default: '' },
})

const emit = defineEmits(['close', 'save'])

const localContent = ref(props.content)

watch(() => props.content, (val) => {
  localContent.value = val
})

function handleSave() {
  emit('save', localContent.value)
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
.edit-modal {
  background: var(--warm-white);
  border-radius: var(--radius);
  padding: 26px;
  width: 100%;
  max-width: 540px;
  max-height: 85vh;
  overflow-y: auto;
}
.em-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.em-header h3 {
  font-size: 18px;
  font-weight: 800;
}
.em-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--gray-pale);
  border: none;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background .15s;
}
.em-close:hover {
  background: var(--gray-light);
}
.em-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--teal);
  margin-bottom: 8px;
}
.em-textarea {
  min-height: 230px;
}
.em-hint {
  font-size: 12px;
  color: var(--gray-mid);
  margin-top: 6px;
  margin-bottom: 16px;
}
.em-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
.em-save {
  width: auto;
  padding: 12px 24px;
}
</style>
