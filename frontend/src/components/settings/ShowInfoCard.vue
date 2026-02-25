<template>
  <div class="card">
    <div class="card-label">🎙️ 節目資訊</div>
    <div class="form-grid">
      <label class="form-field full">
        <span>節目名稱</span>
        <input class="inp" v-model="settings.showName" placeholder="我的 Podcast" />
      </label>
      <label class="form-field full">
        <span>節目簡介</span>
        <textarea class="inp" v-model="settings.showDesc" rows="3" placeholder="用一兩句話介紹你的節目..."></textarea>
      </label>
      <label class="form-field">
        <span>作者</span>
        <input class="inp" v-model="settings.author" placeholder="你的名字" />
      </label>
      <label class="form-field">
        <span>Email</span>
        <input class="inp" v-model="settings.email" type="email" placeholder="you@example.com" />
      </label>
      <label class="form-field">
        <span>網站</span>
        <input class="inp" v-model="settings.website" placeholder="https://..." />
      </label>
      <label class="form-field">
        <span>分類</span>
        <select class="inp" v-model="settings.category">
          <option value="">選擇分類</option>
          <option value="technology">科技</option>
          <option value="education">教育</option>
          <option value="society">社會與文化</option>
          <option value="business">商業</option>
          <option value="entertainment">娛樂</option>
          <option value="health">健康</option>
        </select>
      </label>
      <label class="form-field">
        <span>語言</span>
        <select class="inp" v-model="settings.language">
          <option value="zh-tw">繁體中文</option>
          <option value="en">English</option>
          <option value="ja">日本語</option>
        </select>
      </label>
      <label class="form-field">
        <span>分級</span>
        <select class="inp" v-model="settings.explicit">
          <option value="clean">一般</option>
          <option value="explicit">限制級</option>
        </select>
      </label>
    </div>
  </div>
</template>

<script setup>
import { useSettingsStore } from '../../stores/settings'

const settings = useSettingsStore()
</script>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.form-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.form-field.full {
  grid-column: 1 / -1;
}
.form-field span {
  font-size: 12px;
  font-weight: 700;
  color: var(--gray-mid);
}

@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
