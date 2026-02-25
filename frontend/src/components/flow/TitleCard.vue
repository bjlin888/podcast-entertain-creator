<template>
  <div
    class="title-card"
    :class="{ selected }"
    @click="$emit('select')"
  >
    <div class="tc-num" :class="{ selected }">{{ index + 1 }}</div>
    <div class="tc-body">
      <div class="tc-zh">{{ title.zh }}</div>
      <div class="tc-en">{{ title.en }}</div>
      <span v-if="title.hook" class="tc-hook">{{ title.hook }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: Object, required: true },
  index: { type: Number, default: 0 },
  selected: { type: Boolean, default: false },
})

defineEmits(['select'])
</script>

<style scoped>
.title-card {
  display: flex;
  gap: 14px;
  padding: 18px;
  background: var(--warm-white);
  border: 2px solid var(--gray-light);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all .2s;
  text-align: left;
}
.title-card:hover {
  border-color: #FF8A50;
  background: #FFFAF5;
  transform: translateY(-2px);
  box-shadow: 0 4px 14px rgba(244,99,30,.1);
}
.title-card.selected {
  border-color: var(--orange);
  background: var(--orange-pale);
  box-shadow: 0 0 0 3px rgba(244,99,30,.14);
}
.tc-num {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--gray-pale);
  color: var(--gray-mid);
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.tc-num.selected {
  background: var(--orange);
  color: #fff;
}
.tc-body {
  flex: 1;
  min-width: 0;
}
.tc-zh {
  font-size: 15px;
  font-weight: 700;
  line-height: 1.4;
  margin-bottom: 4px;
}
.tc-en {
  font-size: 13px;
  color: var(--gray-mid);
  margin-bottom: 6px;
}
.tc-hook {
  display: inline-block;
  font-size: 11px;
  padding: 2px 9px;
  border-radius: 99px;
  background: var(--teal-light);
  color: var(--teal);
  font-weight: 600;
}
</style>
