import { ref } from 'vue'

const BASE_URL = ''

/**
 * Get or create a persistent user ID from localStorage.
 */
function getUserId() {
  let id = localStorage.getItem('podcast_user_id')
  if (!id) {
    id = crypto.randomUUID ? crypto.randomUUID() : generateUUID()
    localStorage.setItem('podcast_user_id', id)
  }
  return id
}

function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

/**
 * Composable for making API calls with automatic X-User-Id header.
 */
export function useApi() {
  const loading = ref(false)
  const error = ref(null)

  async function request(endpoint, options = {}) {
    loading.value = true
    error.value = null

    const url = `${BASE_URL}${endpoint}`
    const headers = {
      'Content-Type': 'application/json',
      'X-User-Id': getUserId(),
      ...(options.headers || {}),
    }

    // Remove Content-Type for FormData
    if (options.body instanceof FormData) {
      delete headers['Content-Type']
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        body: options.body instanceof FormData
          ? options.body
          : options.body
            ? JSON.stringify(options.body)
            : undefined,
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.detail || errData.message || `HTTP ${response.status}`)
      }

      const data = await response.json()
      return data
    } catch (err) {
      error.value = err.message || 'Network error'
      throw err
    } finally {
      loading.value = false
    }
  }

  // Convenience methods
  async function get(endpoint) {
    return request(endpoint, { method: 'GET' })
  }

  async function post(endpoint, body) {
    return request(endpoint, { method: 'POST', body })
  }

  async function patch(endpoint, body) {
    return request(endpoint, { method: 'PATCH', body })
  }

  async function del(endpoint) {
    return request(endpoint, { method: 'DELETE' })
  }

  async function upload(endpoint, formData) {
    return request(endpoint, { method: 'POST', body: formData })
  }

  return {
    loading,
    error,
    get,
    post,
    patch,
    del,
    upload,
    getUserId,
  }
}
