import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

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
  const llmKey = ref(stored.llmKey || '')
  const ttsProvider = ref(stored.ttsProvider || 'gemini')
  const ttsKey = ref(stored.ttsKey || '')

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

  // Save all
  function saveAll() {
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
      llmKey: llmKey.value,
      ttsProvider: ttsProvider.value,
      ttsKey: ttsKey.value,
    }
    saveToStorage(data)
  }

  // Auto-save when any value changes
  const allRefs = [
    showName, showDesc, author, email, website, category, language, explicit,
    googleEnabled, googleRss, googleVerify, googleInterval,
    appleEnabled, appleId, appleProviderId, appleKey, appleKeyId, appleTeamId, appleRss,
    llmProvider, llmModel, llmKey, ttsProvider, ttsKey,
  ]
  allRefs.forEach(r => {
    watch(r, () => saveAll(), { deep: true })
  })

  return {
    showName, showDesc, author, email, website, category, language, explicit,
    googleEnabled, googleRss, googleVerify, googleInterval,
    appleEnabled, appleId, appleProviderId, appleKey, appleKeyId, appleTeamId, appleRss,
    llmProvider, llmModel, llmKey, ttsProvider, ttsKey,
    googleStatus, appleStatus, getLLMModels, saveAll,
  }
})
