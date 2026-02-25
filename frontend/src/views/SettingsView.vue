<template>
  <div>
    <section class="settings-hero">
      <div class="sh-orb sh-teal"></div>
      <div class="sh-orb sh-orange"></div>
      <div class="sh-deco">⚙️</div>
      <div class="sh-eyebrow">Settings</div>
      <h1 class="sh-title">系統設定</h1>
    </section>

    <div class="settings-main">
      <h2 class="sec-heading">
        <span>🎙️ 節目資訊</span>
        <span class="sec-line"></span>
      </h2>
      <ShowInfoCard />

      <h2 class="sec-heading">
        <span>📡 發佈平台</span>
        <span class="sec-line"></span>
      </h2>
      <PlatformCard platform="google" />
      <PlatformCard platform="apple" />

      <h2 class="sec-heading">
        <span>🤖 AI 設定</span>
        <span class="sec-line"></span>
      </h2>
      <AiConfigCard />
    </div>
  </div>
</template>

<script setup>
import ShowInfoCard from '../components/settings/ShowInfoCard.vue'
import PlatformCard from '../components/settings/PlatformCard.vue'
import AiConfigCard from '../components/settings/AiConfigCard.vue'
</script>

<style scoped>
.settings-hero {
  position: relative;
  background: var(--ink-soft);
  padding: 44px 28px 36px;
  text-align: center;
  overflow: hidden;
}
.sh-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  pointer-events: none;
}
.sh-teal {
  width: 160px;
  height: 160px;
  background: var(--teal);
  opacity: .12;
  bottom: -40px;
  left: 20%;
}
.sh-orange {
  width: 140px;
  height: 140px;
  background: var(--orange);
  opacity: .1;
  top: -30px;
  right: 15%;
}
.sh-deco {
  position: absolute;
  top: 10px;
  right: 60px;
  font-size: 80px;
  opacity: .05;
  transform: rotate(-8deg);
  pointer-events: none;
}
.sh-eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: var(--teal);
  margin-bottom: 8px;
}
.sh-title {
  font-family: var(--font-display);
  font-size: 34px;
  font-weight: 700;
  color: #fff;
}

.settings-main {
  max-width: 760px;
  margin: 0 auto;
  padding: 28px 24px 80px;
}
.sec-heading {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: 800;
  margin: 28px 0 14px;
}
.sec-heading:first-of-type {
  margin-top: 0;
}
.sec-line {
  flex: 1;
  height: 1.5px;
  background: var(--gray-light);
}

@media (max-width: 640px) {
  .settings-hero {
    padding: 32px 14px 28px;
  }
  .sh-title {
    font-size: 26px;
  }
  .settings-main {
    padding-left: 14px;
    padding-right: 14px;
  }
}
</style>
