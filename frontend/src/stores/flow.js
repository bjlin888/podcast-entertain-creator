import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useApi } from '../composables/useApi'
import { useEpisodesStore } from './episodes'

export const useFlowStore = defineStore('flow', () => {
  // Current project
  const projectId = ref(null)
  const currentStep = ref(1)

  // Step 1: Topic
  const topic = ref('')
  const audience = ref([])
  const duration = ref('30 分鐘')
  const style = ref('輕鬆聊天')
  const hostCount = ref('我一人')

  // Step 2: Titles
  const titles = ref([])
  const selectedTitleIndex = ref(-1)

  // Step 3: Script / Segments
  const segments = ref([])
  const scriptId = ref(null)

  // Step 4: Feedback
  const ratings = ref({ naturalness: 0, pacing: 0, style: 0 })
  const feedbackText = ref('')

  // Step 5: Export
  const fullScript = ref('')
  const audioFiles = ref([])

  // Voice config
  const voiceConfig = ref({
    voice: 'female', speed: 'normal', pitch: 'normal', ttsProvider: 'gemini', stylePrompt: '',
    speakers: [
      { name: '主持人A', voice: 'Achird' },
      { name: '主持人B', voice: 'Kore' },
    ],
  })

  // Loading
  const isLoading = ref(false)
  const loadingText = ref('')
  const loadingSub = ref('')

  // Progress percentage per step
  const progressPercent = computed(() => {
    return currentStep.value * 20
  })

  // Is next step enabled?
  const canProceed = computed(() => {
    switch (currentStep.value) {
      case 1: return topic.value.trim().length > 0
      case 2: return selectedTitleIndex.value >= 0
      case 3: return segments.value.length > 0
      case 4: return true
      case 5: return true
      default: return false
    }
  })

  // ─── Actions ─── //

  async function fetchAndLoad(projectId_) {
    const api = useApi()
    const data = await api.get(`/api/v1/projects/${projectId_}`)

    const project = data.project || data

    // Basic fields
    projectId.value = project.project_id || project.id || projectId_
    topic.value = project.topic || ''
    audience.value = project.audience
      ? (Array.isArray(project.audience) ? project.audience : project.audience.split(',').map(s => s.trim()).filter(Boolean))
      : []
    duration.value = project.duration_min ? `${project.duration_min} 分鐘` : '30 分鐘'
    style.value = project.style || '輕鬆聊天'
    hostCount.value = project.host_count === 2
      ? '雙人對談'
      : project.host_count >= 3 ? '多人' : '我一人'

    // Titles
    titles.value = (data.titles || []).map(mapTitle)
    selectedTitleIndex.value = data.titles
      ? data.titles.findIndex(t => t.is_selected === 1 || t.is_selected === true)
      : -1

    // Script / Segments
    scriptId.value = data.script?.script_id || null
    segments.value = (data.segments || []).map(mapSegment)

    // Merge audio data (voice_samples) into segments
    if (segments.value.length > 0 && scriptId.value) {
      try {
        const audioData = await api.get(`/api/v1/projects/${projectId_}/export/audio`)
        for (const af of (audioData.audio_files || [])) {
          const seg = segments.value[af.segment_order]
          if (seg) {
            seg.audioUrl = af.tts_url || null
            seg.hostAudioUrl = af.host_audio_url || null
            seg.sampleId = af.sample_id || null
          }
        }
      } catch {
        // Audio data not available, continue without it
      }
    }

    // Infer step from data availability
    let inferredStep = 1
    if (segments.value.length > 0) inferredStep = 3
    else if (titles.value.length > 0) inferredStep = 2
    else if (topic.value) inferredStep = 1

    // Use backend step if it's more advanced
    const backendStep = project.step || 0
    currentStep.value = Math.max(inferredStep, backendStep)

    // Reset transient state
    ratings.value = { naturalness: 0, pacing: 0, style: 0 }
    feedbackText.value = ''
    fullScript.value = ''
    audioFiles.value = []
  }

  function loadEpisode(episode) {
    projectId.value = episode.id
    topic.value = episode.topic || ''
    audience.value = episode.audience ? (Array.isArray(episode.audience) ? episode.audience : [episode.audience]) : []
    duration.value = episode.dur || '30 分鐘'
    style.value = episode.style || '輕鬆聊天'
    hostCount.value = episode.hostCount || '我一人'
    titles.value = episode.titles || []
    selectedTitleIndex.value = episode.selTitle ?? -1
    segments.value = episode.segments ? JSON.parse(JSON.stringify(episode.segments)) : []
    currentStep.value = episode.step || 1
    ratings.value = { naturalness: 0, pacing: 0, style: 0 }
    feedbackText.value = ''
    fullScript.value = ''
    audioFiles.value = []
  }

  function saveToEpisodeStore() {
    const store = useEpisodesStore()
    if (!projectId.value) return

    const stepProgressMap = { 1: 5, 2: 30, 3: 60, 4: 80, 5: 100 }
    const progress = stepProgressMap[currentStep.value] || 0

    let title = '(新集數)'
    if (selectedTitleIndex.value >= 0 && titles.value[selectedTitleIndex.value]) {
      title = titles.value[selectedTitleIndex.value].zh
    } else if (topic.value) {
      title = topic.value.slice(0, 22) + (topic.value.length > 22 ? '...' : '')
    }

    store.updateEpisode(projectId.value, {
      topic: topic.value,
      style: style.value,
      dur: duration.value,
      audience: audience.value,
      hostCount: hostCount.value,
      titles: titles.value,
      selTitle: selectedTitleIndex.value,
      segments: JSON.parse(JSON.stringify(segments.value)),
      step: currentStep.value,
      progress,
      status: currentStep.value >= 5 ? 'done' : 'draft',
      title,
    })

    // Sync step/progress to backend (fire-and-forget)
    const api = useApi()
    api.patch(`/api/v1/projects/${projectId.value}`, {
      step: currentStep.value,
      progress,
      status: currentStep.value >= 5 ? 'done' : 'draft',
    }).catch(() => {})
  }

  // Step 1 -> 2: Generate titles
  async function generateTitles() {
    const api = useApi()
    isLoading.value = true
    loadingText.value = 'AI 正在構思標題...'
    loadingSub.value = '幫你想 5 個吸引人的好標題'

    try {
      // Save topic to backend first
      await api.patch(`/api/v1/projects/${projectId.value}`, {
        topic: topic.value,
        audience: audience.value.join(','),
        duration_min: parseDuration(duration.value),
        style: style.value,
        host_count: parseHostCount(hostCount.value),
      })

      const data = await api.post(`/api/v1/projects/${projectId.value}/titles/generate`, {})
      titles.value = (data.titles || []).map(mapTitle)
      selectedTitleIndex.value = -1
      currentStep.value = 2
      saveToEpisodeStore()
    } catch {
      // Fallback: demo titles
      titles.value = getDemoTitles()
      selectedTitleIndex.value = -1
      currentStep.value = 2
      saveToEpisodeStore()
    } finally {
      isLoading.value = false
    }
  }

  async function regenerateTitles() {
    const api = useApi()
    isLoading.value = true
    loadingText.value = '重新發想標題中...'
    loadingSub.value = '換一批全新的角度'

    try {
      const data = await api.post(`/api/v1/projects/${projectId.value}/titles/generate`, {})
      titles.value = (data.titles || []).map(mapTitle)
      selectedTitleIndex.value = -1
    } catch {
      titles.value = getDemoTitles()
      selectedTitleIndex.value = -1
    } finally {
      isLoading.value = false
    }
  }

  function selectTitle(index) {
    selectedTitleIndex.value = index
    // Attempt to notify backend
    const api = useApi()
    if (titles.value[index]?.id) {
      api.post(`/api/v1/projects/${projectId.value}/titles/${titles.value[index].id}/select`, {}).catch(() => {})
    }
  }

  // Step 2 -> 3: Generate script
  async function generateScript() {
    const api = useApi()
    isLoading.value = true
    loadingText.value = 'AI 正在撰寫腳本...'
    loadingSub.value = '依照你的主題生成完整腳本，請稍候'

    try {
      const data = await api.post(`/api/v1/projects/${projectId.value}/scripts/generate`, {})
      scriptId.value = data.script?.script_id || null
      segments.value = (data.segments || []).map(mapSegment)
      currentStep.value = 3
      saveToEpisodeStore()
    } catch {
      segments.value = getDemoSegments()
      currentStep.value = 3
      saveToEpisodeStore()
    } finally {
      isLoading.value = false
    }
  }

  // Segment operations
  async function updateSegment(segIndex, newContent) {
    const seg = segments.value[segIndex]
    if (!seg) return

    const api = useApi()
    try {
      if (seg.id) {
        await api.patch(`/api/v1/scripts/segments/${seg.id}`, { content: newContent })
      }
    } catch {
      // Continue with local update
    }
    segments.value[segIndex] = { ...seg, content: newContent }
    saveToEpisodeStore()
  }

  async function refineSegment(segIndex) {
    const seg = segments.value[segIndex]
    if (!seg || !seg.id) return

    const api = useApi()
    isLoading.value = true
    loadingText.value = 'AI 重寫中...'
    loadingSub.value = '優化這個段落的內容'

    try {
      const data = await api.post(`/api/v1/scripts/segments/${seg.id}/refine`, { content: '' })
      if (data.segment?.content) {
        segments.value[segIndex] = { ...seg, content: data.segment.content, id: data.segment.segment_id || seg.id }
      }
      saveToEpisodeStore()
    } catch {
      // No-op
    } finally {
      isLoading.value = false
    }
  }

  async function generateTTS(segIndex) {
    const seg = segments.value[segIndex]
    if (!seg || !seg.id) return null

    const api = useApi()
    isLoading.value = true
    loadingText.value = '生成示範音檔中...'
    const voiceLabel = voiceConfig.value.voice === 'female' ? '女聲' : '男聲'
    const speedLabel = { slow: '慢速', normal: '正常', fast: '快速' }[voiceConfig.value.speed]
    loadingSub.value = `${voiceLabel} · ${speedLabel} · 台灣口音`

    try {
      const ttsPayload = voiceConfig.value.ttsProvider === 'gemini'
        ? {
            voice: voiceConfig.value.voice,
            tts_provider: 'gemini',
            style_prompt: voiceConfig.value.stylePrompt || '',
          }
        : {
            voice: mapVoice(voiceConfig.value.voice),
            speed: mapSpeed(voiceConfig.value.speed),
            pitch: mapPitch(voiceConfig.value.pitch),
            tts_provider: 'google',
          }
      const data = await api.post(`/api/v1/scripts/segments/${seg.id}/tts`, ttsPayload)
      // Store sample_id on segment for host audio upload
      if (data.sample_id) {
        segments.value[segIndex] = { ...seg, sampleId: data.sample_id, audioUrl: data.tts_url }
      }
      return data
    } catch {
      // Return a simulated result
      return { sample_id: 'demo', audio_url: null }
    } finally {
      isLoading.value = false
    }
  }

  async function generateMultiSpeakerTTS({ speakers, stylePrompt, ttsProvider } = {}) {
    if (!scriptId.value) return null

    const api = useApi()
    isLoading.value = true
    loadingText.value = '生成多人對話音檔中...'
    loadingSub.value = '使用 Gemini 多人語音合成整集音檔'

    try {
      const payload = {
        speakers: speakers || voiceConfig.value.speakers,
        style_prompt: stylePrompt || voiceConfig.value.stylePrompt || '',
        tts_provider: ttsProvider || 'gemini',
      }
      const data = await api.post(`/api/v1/scripts/${scriptId.value}/tts-multi`, payload)
      return data
    } catch {
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function uploadHostAudio(segIndex, file) {
    const seg = segments.value[segIndex]
    if (!seg || !seg.sampleId) return null

    const api = useApi()
    const formData = new FormData()
    formData.append('file', file)

    try {
      const data = await api.upload(`/api/v1/voice-samples/${seg.sampleId}/host-audio`, formData)
      if (data.host_audio_url) {
        segments.value[segIndex] = { ...seg, hostAudioUrl: data.host_audio_url }
      }
      return data
    } catch {
      return null
    }
  }

  // Step 4: Feedback
  async function submitFeedback() {
    const api = useApi()
    isLoading.value = true
    loadingText.value = 'AI 根據你的意見優化腳本...'
    loadingSub.value = '正在重新生成更好的版本'

    try {
      const data = await api.post(`/api/v1/projects/${projectId.value}/feedback`, {
        score_content: ratings.value.naturalness,
        score_engagement: ratings.value.pacing,
        score_structure: ratings.value.style,
        text_feedback: feedbackText.value,
      })

      if (data.regenerated && data.segments) {
        segments.value = (data.segments).map(mapSegment)
      }

      // Go back to script step for review
      currentStep.value = 3
      saveToEpisodeStore()
    } catch {
      // Just go back to script review
      currentStep.value = 3
      saveToEpisodeStore()
    } finally {
      isLoading.value = false
    }
  }

  // Step 5: Export
  async function goToExport() {
    currentStep.value = 5
    saveToEpisodeStore()
    await buildFullScript()
  }

  async function buildFullScript() {
    const api = useApi()
    try {
      const data = await api.get(`/api/v1/projects/${projectId.value}/export/script`)
      fullScript.value = data.text || buildLocalScript()
    } catch {
      fullScript.value = buildLocalScript()
    }
  }

  function buildLocalScript() {
    return segments.value.map(seg => {
      return `【${seg.label || seg.id}】\n${seg.content}`
    }).join('\n\n---\n\n')
  }

  async function fetchAudioExport() {
    const api = useApi()
    try {
      const data = await api.get(`/api/v1/projects/${projectId.value}/export/audio`)
      audioFiles.value = data.audio_files || []
    } catch {
      audioFiles.value = []
    }
  }

  function copyScript() {
    const text = fullScript.value || buildLocalScript()
    navigator.clipboard.writeText(text).catch(() => {})
  }

  function downloadScript() {
    const text = fullScript.value || buildLocalScript()
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `podcast-script-${projectId.value}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  function reset() {
    projectId.value = null
    currentStep.value = 1
    topic.value = ''
    audience.value = []
    duration.value = '30 分鐘'
    style.value = '輕鬆聊天'
    hostCount.value = '我一人'
    titles.value = []
    selectedTitleIndex.value = -1
    segments.value = []
    scriptId.value = null
    ratings.value = { naturalness: 0, pacing: 0, style: 0 }
    feedbackText.value = ''
    fullScript.value = ''
    audioFiles.value = []
  }

  // ─── Mapping helpers ─── //
  function parseDuration(dur) {
    const match = dur.match(/(\d+)/)
    return match ? parseInt(match[1], 10) : 30
  }

  function parseHostCount(hc) {
    if (hc === '我一人') return 1
    if (hc === '雙人對談') return 2
    return 3
  }

  function mapVoice(v) {
    return v === 'male' ? 'cmn-TW-Wavenet-B' : 'cmn-TW-Wavenet-A'
  }

  function mapSpeed(s) {
    return { slow: 0.8, normal: 1.0, fast: 1.25 }[s] || 1.0
  }

  function mapPitch(p) {
    return { low: -2.0, normal: 0.0, high: 2.0 }[p] || 0.0
  }

  // Map backend title to frontend format
  function mapTitle(t) {
    if (!t) return t
    return {
      id: t.title_id || t.id,
      zh: t.title_zh || t.zh,
      en: t.title_en || t.en,
      hook: t.hook || '',
    }
  }

  // Map backend segment to frontend format
  const segTypeMap = { opening: 'intro', main: 'seg', closing: 'outro' }
  const segLabelMap = { opening: '開場白', main: '內容段', closing: '結尾' }

  function mapSegment(s) {
    if (!s) return s
    return {
      id: s.segment_id || s.id,
      tag: segTypeMap[s.segment_type] || s.tag || 'seg',
      label: segLabelMap[s.segment_type] || s.label || s.segment_type || '',
      content: s.content || '',
      cues: typeof s.cues === 'string' ? JSON.parse(s.cues || '[]') : (s.cues || []),
      dur: s.dur || '',
      audioUrl: s.audioUrl || null,
      hostAudioUrl: s.hostAudioUrl || null,
      sampleId: s.sampleId || null,
    }
  }

  // ─── Demo data fallbacks ─── //
  function getDemoTitles() {
    const all = [
      { zh: '你知道 AI 其實正在幫你省下幾十個小時嗎？', en: 'How AI Is Secretly Saving You Dozens of Hours', hook: '反差感強，讓人想繼續聽' },
      { zh: '5 個我每天用的 AI 工具，用了就回不去', en: "5 AI Tools I Use Daily and Can't Live Without", hook: '數字開頭，具體又實用' },
      { zh: '別再說 AI 搶工作了，它其實在幫你加薪', en: "Stop Saying AI Steals Jobs — It's Giving You Raises", hook: '顛覆常見誤解，製造好奇' },
      { zh: '這些 AI 工具我試了一個月，老實說結果很意外', en: 'I Tested These AI Tools for a Month — Honest Results', hook: '親身實測，真誠感強' },
      { zh: 'AI 時代每個人都該懂的 3 個基本觀念', en: '3 Fundamental AI Concepts Everyone Should Know', hook: '適合所有人，降低進入門檻' },
    ]
    return all.sort(() => Math.random() - 0.5)
  }

  function getDemoSegments() {
    return [
      {
        id: 'INTRO', label: '開場白', tag: 'intro', dur: '約 30 秒',
        content: '嗨大家好，歡迎回來我的 Podcast！\n\n（停頓）\n\n你有沒有這種感覺？身邊的人都在說 AI、用 AI，但打開了一堆工具，反而覺得更混亂？今天這集，我們就來好好說清楚。',
        cues: ['（停頓）', '【BGM淡入】'],
      },
      {
        id: 'SEGMENT_1', label: '為什麼現在要聊 AI？', tag: 'seg', dur: '約 5 分鐘',
        content: '先說說我自己的故事。（加強語氣）三個月前，我一天花在整理資料上的時間超過兩個小時。但現在，同樣的事情只要 15 分鐘。\n\n這不是魔法，是找到了適合自己的 AI 工作流程。',
        cues: ['（加強語氣）', '（停頓）'],
      },
      {
        id: 'SEGMENT_2', label: '5 個推薦工具介紹', tag: 'seg', dur: '約 15 分鐘',
        content: '好，直接進入正題。第一個工具是 Claude，它是我目前最常用的 AI 助理。\n\n（停頓）\n\n為什麼選 Claude？因為它在理解中文、回覆台灣口語方面表現特別好。',
        cues: ['（停頓）'],
      },
      {
        id: 'OUTRO', label: '結尾與行動呼籲', tag: 'outro', dur: '約 1 分鐘',
        content: '今天跟大家分享了我最愛用的 5 個 AI 工具。希望你不只是覺得「有趣」，而是今天就去試試！\n\n（停頓）\n\n記得訂閱，我們下集見！',
        cues: ['（停頓）', '（加強語氣）'],
      },
    ]
  }

  return {
    projectId,
    currentStep,
    topic,
    audience,
    duration,
    style,
    hostCount,
    titles,
    selectedTitleIndex,
    segments,
    scriptId,
    ratings,
    feedbackText,
    fullScript,
    audioFiles,
    voiceConfig,
    isLoading,
    loadingText,
    loadingSub,
    progressPercent,
    canProceed,
    fetchAndLoad,
    loadEpisode,
    saveToEpisodeStore,
    generateTitles,
    regenerateTitles,
    selectTitle,
    generateScript,
    updateSegment,
    refineSegment,
    generateTTS,
    generateMultiSpeakerTTS,
    uploadHostAudio,
    submitFeedback,
    goToExport,
    buildFullScript,
    fetchAudioExport,
    copyScript,
    downloadScript,
    reset,
  }
})
