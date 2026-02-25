import { ref } from 'vue'

const message = ref('')
const visible = ref(false)
let hideTimer = null

/**
 * Composable for toast notifications.
 * Singleton state shared across all components.
 */
export function useToast() {
  function show(msg, duration = 2800) {
    if (hideTimer) clearTimeout(hideTimer)
    message.value = msg
    visible.value = true

    hideTimer = setTimeout(() => {
      visible.value = false
      hideTimer = null
    }, duration)
  }

  function hide() {
    if (hideTimer) clearTimeout(hideTimer)
    visible.value = false
    hideTimer = null
  }

  return {
    message,
    visible,
    show,
    hide,
  }
}
