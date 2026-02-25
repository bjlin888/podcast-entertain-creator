<template>
  <div class="star-rating">
    <span class="sr-label">{{ label }}</span>
    <div class="sr-stars">
      <button
        v-for="n in 5"
        :key="n"
        class="sr-star"
        :class="{ active: n <= modelValue }"
        @click="$emit('update:modelValue', n)"
      >⭐</button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, default: '' },
  modelValue: { type: Number, default: 0 },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.star-rating {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
}
.sr-label {
  font-size: 14px;
  font-weight: 600;
}
.sr-stars {
  display: flex;
  gap: 4px;
}
.sr-star {
  background: none;
  border: none;
  font-size: 26px;
  cursor: pointer;
  filter: grayscale(1);
  opacity: .4;
  transition: all .15s;
  padding: 2px;
}
.sr-star:hover {
  transform: scale(1.15);
}
.sr-star.active {
  filter: none;
  opacity: 1;
  transform: scale(1.2);
}
</style>
