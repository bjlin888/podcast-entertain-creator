import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { useApi } from '../composables/useApi'

const STORAGE_KEY = 'podcast_settings'

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function saveToStorage(data) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch {
    // Storage full or unavailable
  }
}

export const useSettingsStore = defineStore('settings', () => {
  const stored = loadFromStorage()

  // Show info
  const showName = ref(stored.showName || '')
  const showDesc = ref(stored.showDesc || '')
  const author = ref(stored.author || '')
  const email = ref(stored.email || '')
  const website = ref(stored.website || '')
  const category = ref(stored.category || '')
  const language = ref(stored.language || 'zh-tw')
  const explicit = ref(stored.explicit || 'clean')

  // Google Podcasts
  const googleEnabled = ref(stored.googleEnabled || false)
  const googleRss = ref(stored.googleRss || '')
  const googleVerify = ref(stored.googleVerify || '')
  const googleInterval = ref(stored.googleInterval || 'auto')

  // Apple Podcasts
  const appleEnabled = ref(stored.appleEnabled || false)
  const appleId = ref(stored.appleId || '')
  const appleProviderId = ref(stored.appleProviderId || '')
  const appleKey = ref(stored.appleKey || '')
  const appleKeyId = ref(stored.appleKeyId || '')
  const appleTeamId = ref(stored.appleTeamId || '')
  const appleRss = ref(stored.appleRss || '')

  // AI config
  const llmProvider = ref(stored.llmProvider || 'claude')
  const llmModel = ref(stored.llmModel || 'claude-sonnet-4-6')
  const llmKey = ref('')  // Never load from storage; input only
  const ttsProvider = ref(stored.ttsProvider || 'gemini')
  const ttsKey = ref('')  // Never load from storage; input only

  // Key status from backend
  const hasGeminiKey = ref(false)
  const hasClaudeKey = ref(false)
  const aiSaving = ref(false)

  // Status helpers
  function googleStatus() {
    if (!googleEnabled.value) return 'none'
    if (googleRss.value) return 'ok'
    return 'pending'
  }

  function appleStatus() {
    if (!appleEnabled.value) return 'none'
    if (appleKey.value && appleKeyId.value) return 'ok'
    return 'pending'
  }

  function getLLMModels() {
    if (llmProvider.value === 'claude') {
      return ['claude-sonnet-4-6', 'claude-opus-4-6']
    }
    return ['gemini-2.5-flash', 'gemini-2.5-pro']
  }

  // Load AI key status from backend
  async function loadAiSettings() {
    const { get } = useApi()
    try {
      const data = await get('/api/v1/settings/ai')
      for (const p of data.providers || []) {
        if (p.provider === 'gemini') {
          hasGeminiKey.value = p.has_key
          if (p.model) llmModel.value = p.model
        }
        if (p.provider === 'claude') {
          hasClaudeKey.value = p.has_key
          if (p.model) llmModel.value = p.model
        }
      }
    } catch {
      // Backend unavailable, ignore
    }
  }

  // Save AI settings to backend
  async function saveAiSettings() {
    const { put } = useApi()
    aiSaving.value = true
    try {
      const providers = []

      // LLM key — determine which provider the key belongs to
      if (llmKey.value) {
        providers.push({
          provider: llmProvider.value,
          api_key: llmKey.value,
          model: llmModel.value || undefined,
        })
      } else if (llmModel.value) {
        // Update model preference only (no key change)
        providers.push({
          provider: llmProvider.value,
          model: llmModel.value,
        })
      }

      // TTS key — Gemini TTS uses same key as Gemini LLM
      if (ttsKey.value && ttsProvider.value === 'gemini') {
        // If user entered a separate TTS key for Gemini, save as gemini provider key
        const existing = providers.find(p => p.provider === 'gemini')
        if (!existing) {
          providers.push({ provider: 'gemini', api_key: ttsKey.value })
        }
      }

      if (providers.length > 0) {
        await put('/api/v1/settings/ai', { providers })
      }

      // Clear key inputs after save
      llmKey.value = ''
      ttsKey.value = ''

      // Refresh status
      await loadAiSettings()
      return true
    } catch {
      return false
    } finally {
      aiSaving.value = false
    }
  }

  // Save all (local + AI backend)
  async function saveAll() {
    const data = {
      showName: showName.value,
      showDesc: showDesc.value,
      author: author.value,
      email: email.value,
      website: website.value,
      category: category.value,
      language: language.value,
      explicit: explicit.value,
      googleEnabled: googleEnabled.value,
      googleRss: googleRss.value,
      googleVerify: googleVerify.value,
      googleInterval: googleInterval.value,
      appleEnabled: appleEnabled.value,
      appleId: appleId.value,
      appleProviderId: appleProviderId.value,
      appleKey: appleKey.value,
      appleKeyId: appleKeyId.value,
      appleTeamId: appleTeamId.value,
      appleRss: appleRss.value,
      llmProvider: llmProvider.value,
      llmModel: llmModel.value,
      ttsProvider: ttsProvider.value,
      // Do NOT persist API keys to localStorage
    }
    saveToStorage(data)
  }

  // Auto-save non-sensitive settings when values change
  const localRefs = [
    showName, showDesc, author, email, website, category, language, explicit,
    googleEnabled, googleRss, googleVerify, googleInterval,
    appleEnabled, appleId, appleProviderId, appleKey, appleKeyId, appleTeamId, appleRss,
    llmProvider, llmModel, ttsProvider,
  ]
  localRefs.forEach(r => {
    watch(r, () => saveAll(), { deep: true })
  })

  return {
    showName, showDesc, author, email, website, category, language, explicit,
    googleEnabled, googleRss, googleVerify, googleInterval,
    appleEnabled, appleId, appleProviderId, appleKey, appleKeyId, appleTeamId, appleRss,
    llmProvider, llmModel, llmKey, ttsProvider, ttsKey,
    hasGeminiKey, hasClaudeKey, aiSaving,
    googleStatus, appleStatus, getLLMModels,
    loadAiSettings, saveAiSettings, saveAll,
  }
})
