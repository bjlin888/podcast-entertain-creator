<template>
  <TopBar />
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
  <ToastNotification />
</template>

<script setup>
import TopBar from './components/TopBar.vue'
import ToastNotification from './components/ToastNotification.vue'
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity .2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
