<template>
  <div class="sec-toolbar">
    <h2 class="sec-title">所有集數</h2>
    <div class="sec-controls">
      <div class="search-wrap" :class="{ focused: searchFocused }">
        <span class="search-icon">🔍</span>
        <input
          class="search-inp"
          type="text"
          placeholder="搜尋集數..."
          :value="searchQuery"
          @input="$emit('update:searchQuery', $event.target.value)"
          @focus="searchFocused = true"
          @blur="searchFocused = false"
        />
      </div>
      <select
        class="sort-sel"
        :value="sortBy"
        @change="$emit('update:sortBy', $event.target.value)"
      >
        <option value="newest">最新優先</option>
        <option value="oldest">最舊優先</option>
        <option value="done">已完成優先</option>
        <option value="draft">進行中優先</option>
      </select>
      <div class="filter-pills">
        <button
          v-for="f in filters"
          :key="f.value"
          class="pill"
          :class="{ active: filter === f.value }"
          @click="$emit('update:filter', f.value)"
        >{{ f.label }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  searchQuery: { type: String, default: '' },
  sortBy: { type: String, default: 'newest' },
  filter: { type: String, default: 'all' },
})

defineEmits(['update:searchQuery', 'update:sortBy', 'update:filter'])

const searchFocused = ref(false)

const filters = [
  { label: '全部', value: 'all' },
  { label: '進行中', value: 'draft' },
  { label: '已完成', value: 'done' },
]
</script>

<style scoped>
.sec-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 18px;
}
.sec-title {
  font-size: 20px;
  font-weight: 900;
}
.sec-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.search-wrap {
  display: flex;
  align-items: center;
  background: var(--warm-white);
  border: 1.5px solid var(--gray-light);
  border-radius: var(--radius-xs);
  padding: 0 10px;
  width: 200px;
  transition: all .2s;
}
.search-wrap.focused {
  width: 240px;
  border-color: var(--orange);
  box-shadow: 0 0 0 3px rgba(244,99,30,.1);
}
.search-icon {
  font-size: 13px;
  margin-right: 6px;
  flex-shrink: 0;
}
.search-inp {
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  font-family: var(--font-body);
  padding: 9px 0;
  width: 100%;
  color: var(--ink);
}
.sort-sel {
  padding: 9px 12px;
  border: 1.5px solid var(--gray-light);
  border-radius: var(--radius-xs);
  background: var(--warm-white);
  font-size: 13px;
  font-family: var(--font-body);
  color: var(--ink);
  cursor: pointer;
  outline: none;
}
.filter-pills {
  display: flex;
  gap: 6px;
}
.pill {
  padding: 7px 14px;
  border: 1.5px solid var(--gray-light);
  border-radius: 99px;
  background: var(--warm-white);
  font-size: 12px;
  font-weight: 700;
  font-family: var(--font-body);
  color: var(--gray-mid);
  cursor: pointer;
  transition: all .15s;
}
.pill:hover {
  border-color: var(--orange);
  color: var(--orange);
}
.pill.active {
  background: var(--orange);
  border-color: var(--orange);
  color: #fff;
}

@media (max-width: 640px) {
  .sec-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }
  .search-wrap,
  .search-wrap.focused {
    width: 100%;
  }
}
</style>
