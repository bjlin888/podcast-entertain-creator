<template>
  <button
    class="opt-btn"
    :class="{ sel: selected }"
    @click="$emit('select')"
  >
    <span class="oi">{{ icon }}</span>
    <span class="ol">{{ label }}</span>
    <span v-if="sublabel" class="os">{{ sublabel }}</span>
  </button>
</template>

<script setup>
defineProps({
  icon: { type: String, default: '' },
  label: { type: String, default: '' },
  sublabel: { type: String, default: '' },
  selected: { type: Boolean, default: false },
})

defineEmits(['select'])
</script>

<style scoped>
.opt-btn {
  padding: 13px 10px;
  border: 2.5px solid var(--gray-light);
  border-radius: var(--radius-sm);
  background: #fff;
  cursor: pointer;
  text-align: center;
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  color: var(--ink);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  transition: all .18s;
}
.oi { font-size: 24px; }
.ol { font-weight: 600; }
.os {
  font-size: 11px;
  color: var(--gray-mid);
}
.opt-btn:hover {
  border-color: #FF8A50;
  background: var(--orange-pale);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(244,99,30,.14);
}
.opt-btn.sel {
  border-color: var(--orange);
  background: var(--orange-pale);
  color: var(--orange);
  font-weight: 700;
  box-shadow: 0 0 0 3px rgba(244,99,30,.14);
}
</style>
