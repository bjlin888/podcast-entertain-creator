<template>
  <button
    class="toggle"
    :class="{ on: modelValue }"
    @click="$emit('update:modelValue', !modelValue)"
    role="switch"
    :aria-checked="modelValue"
  >
    <span class="toggle-knob"></span>
  </button>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.toggle {
  width: 42px;
  height: 24px;
  border-radius: 12px;
  background: var(--gray-light);
  border: none;
  padding: 2px;
  cursor: pointer;
  position: relative;
  transition: background .2s;
  flex-shrink: 0;
}
.toggle.on {
  background: var(--teal);
}
.toggle-knob {
  display: block;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,.15);
  transition: transform .2s;
}
.toggle.on .toggle-knob {
  transform: translateX(18px);
}
</style>
