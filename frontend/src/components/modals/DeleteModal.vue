<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-backdrop" @click.self="$emit('close')">
      <div class="delete-modal anim-pop">
        <div class="dm-icon">🗑️</div>
        <h3 class="dm-title">確定要刪除嗎？</h3>
        <p class="dm-desc">
          「{{ title }}」將被永久刪除，此操作無法復原。
        </p>
        <div class="dm-actions">
          <button class="btn-secondary" @click="$emit('close')">取消</button>
          <button class="dm-del" @click="$emit('confirm')">刪除</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '' },
})

defineEmits(['close', 'confirm'])
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
.delete-modal {
  background: var(--warm-white);
  border-radius: var(--radius);
  padding: 32px 28px;
  width: 100%;
  max-width: 380px;
  text-align: center;
}
.dm-icon {
  font-size: 44px;
  margin-bottom: 12px;
}
.dm-title {
  font-size: 20px;
  font-weight: 800;
  margin-bottom: 8px;
}
.dm-desc {
  font-size: 14px;
  color: var(--gray-mid);
  margin-bottom: 22px;
  line-height: 1.5;
}
.dm-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}
.dm-del {
  padding: 11px 24px;
  background: #E53E3E;
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 700;
  font-family: var(--font-body);
  cursor: pointer;
  transition: all .18s;
}
.dm-del:hover {
  background: #C53030;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(229,62,62,.3);
}
</style>
