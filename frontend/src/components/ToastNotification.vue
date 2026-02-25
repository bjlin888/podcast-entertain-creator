<template>
  <Teleport to="body">
    <div class="toast" :class="{ on: visible }">
      {{ message }}
    </div>
  </Teleport>
</template>

<script setup>
import { useToast } from '../composables/useToast'

const { message, visible } = useToast()
</script>

<style scoped>
.toast {
  position: fixed;
  bottom: 28px;
  left: 50%;
  transform: translateX(-50%) translateY(80px);
  background: var(--ink);
  color: #fff;
  padding: 13px 22px;
  border-radius: 99px;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 8px 32px rgba(0,0,0,.25);
  z-index: 300;
  transition: transform .33s cubic-bezier(.4,0,.2,1);
  white-space: nowrap;
  pointer-events: none;
}
.toast.on {
  transform: translateX(-50%) translateY(0);
}
</style>
