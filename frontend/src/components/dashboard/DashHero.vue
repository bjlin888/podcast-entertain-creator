<template>
  <section class="hero">
    <div class="hero-deco">🎙</div>
    <div class="hero-orb orb-orange"></div>
    <div class="hero-orb orb-teal"></div>
    <div class="hero-eyebrow">Podcast Creator</div>
    <h1 class="hero-title">打造你的 Podcast 腳本</h1>
    <button class="hero-cta" @click="$emit('new-episode')">
      ＋ 建立新的一集
    </button>
    <span class="hero-hint">按 <kbd>N</kbd> 快速建立</span>
  </section>
</template>

<script setup>
defineEmits(['new-episode'])
</script>

<style scoped>
.hero {
  position: relative;
  background: var(--ink-soft);
  border-radius: var(--radius);
  padding: 52px 36px 44px;
  margin-bottom: 28px;
  overflow: hidden;
  text-align: center;
}
.hero-deco {
  position: absolute;
  top: -10px;
  right: 40px;
  font-size: 120px;
  opacity: .055;
  transform: rotate(12deg);
  pointer-events: none;
}
.hero-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  pointer-events: none;
}
.orb-orange {
  width: 200px;
  height: 200px;
  background: var(--orange);
  opacity: .18;
  top: -60px;
  right: -40px;
}
.orb-teal {
  width: 180px;
  height: 180px;
  background: var(--teal);
  opacity: .13;
  bottom: -50px;
  left: -30px;
}
.hero-eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: var(--orange);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.hero-eyebrow::before {
  content: '';
  width: 22px;
  height: 3px;
  background: var(--orange);
  border-radius: 2px;
}
.hero-title {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 22px;
  line-height: 1.2;
}
.hero-cta {
  padding: 15px 32px;
  background: var(--orange);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 16px;
  font-weight: 700;
  font-family: var(--font-body);
  cursor: pointer;
  box-shadow: 0 4px 18px rgba(244,99,30,.35);
  transition: all .2s;
}
.hero-cta:hover {
  background: #FF7A3A;
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(244,99,30,.45);
}
.hero-hint {
  display: block;
  margin-top: 11px;
  font-size: 12px;
  color: rgba(255,255,255,.4);
}
.hero-hint kbd {
  background: rgba(255,255,255,.12);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--font-body);
  font-size: 11px;
}

@media (max-width: 640px) {
  .hero {
    padding: 36px 20px 32px;
  }
  .hero-title {
    font-size: 28px;
  }
}
</style>
