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

  // Generation tracking — to skip regeneration when input hasn't changed
  const lastGeneratedTopic = ref('')
  const lastGeneratedTitleId = ref(null)

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

    // Initialize generation tracking for loaded projects
    if (titles.value.length > 0) lastGeneratedTopic.value = topic.value
    if (segments.value.length > 0 && selectedTitleIndex.value >= 0) {
      lastGeneratedTitleId.value = titles.value[selectedTitleIndex.value]?.id || null
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
      lastGeneratedTopic.value = topic.value
      currentStep.value = 2
      saveToEpisodeStore()
    } catch {
      // Fallback: demo titles
      titles.value = getDemoTitles()
      selectedTitleIndex.value = -1
      lastGeneratedTopic.value = topic.value
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
      lastGeneratedTitleId.value = titles.value[selectedTitleIndex.value]?.id || null
      currentStep.value = 3
      saveToEpisodeStore()
    } catch {
      segments.value = getDemoSegments()
      lastGeneratedTitleId.value = titles.value[selectedTitleIndex.value]?.id || null
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
    lastGeneratedTopic.value = ''
    lastGeneratedTitleId.value = null
    ratings.value = { naturalness: 0, pacing: 0, style: 0 }
    feedbackText.value = ''
    fullScript.value = ''
    audioFiles.value = []
  }

  // ─── Skip-generation checks ─── //
  function canSkipTitleGeneration() {
    return titles.value.length > 0 && topic.value === lastGeneratedTopic.value
  }

  function canSkipScriptGeneration() {
    if (segments.value.length === 0) return false
    const currentTitleId = titles.value[selectedTitleIndex.value]?.id || null
    return currentTitleId != null && currentTitleId === lastGeneratedTitleId.value
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

  // Map segment_type to layer (opening / main / closing)
  const segLayerMap = {
    cold_open: 'opening', jingle: 'opening', host_intro: 'opening',
    topic_intro: 'main', core_1: 'main', core_2: 'main', ad_break: 'main',
    summary: 'closing', cta: 'closing', preview: 'closing',
    // Legacy fallbacks
    opening: 'opening', main: 'main', closing: 'closing',
  }

  // Map segment_type to CSS tag class
  const segTagMap = {
    cold_open: 'cold-open', jingle: 'jingle', host_intro: 'host-intro',
    topic_intro: 'topic-intro', core_1: 'core', core_2: 'core', ad_break: 'ad-break',
    summary: 'summary', cta: 'cta', preview: 'preview',
    // Legacy fallbacks
    opening: 'intro', main: 'seg', closing: 'outro',
  }

  // Default Chinese labels for all 10 types
  const segDefaultLabelMap = {
    cold_open: '冷開場', jingle: '品牌 Jingle', host_intro: '主持人介紹',
    topic_intro: '主題引入', core_1: '核心內容一', core_2: '核心內容二', ad_break: '廣告/互動',
    summary: '重點摘要', cta: '行動呼籲', preview: '下集預告',
    // Legacy fallbacks
    opening: '開場白', main: '內容段', closing: '結尾',
  }

  function mapSegment(s) {
    if (!s) return s
    const segType = s.segment_type || 'main'
    return {
      id: s.segment_id || s.id,
      segmentType: segType,
      tag: segTagMap[segType] || s.tag || 'seg',
      label: s.label || segDefaultLabelMap[segType] || s.segment_type || '',
      layer: segLayerMap[segType] || 'main',
      content: s.content || '',
      cues: typeof s.cues === 'string' ? JSON.parse(s.cues || '[]') : (s.cues || []),
      dur: s.estimated_duration || s.dur || '',
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
        id: 'COLD_OPEN', segmentType: 'cold_open', label: '冷開場：驚人數據', tag: 'cold-open', layer: 'opening', dur: '約 15 秒',
        content: '你知道嗎？有 78% 的人說自己在用 AI，但其中只有 12% 真的用對了方法。今天這集，我們要來揭開這個巨大的落差。',
        cues: ['[BGM fade in]'],
      },
      {
        id: 'JINGLE', segmentType: 'jingle', label: '品牌 Jingle', tag: 'jingle', layer: 'opening', dur: '約 5 秒',
        content: '[品牌開場音樂]',
        cues: ['[Jingle 播放]'],
      },
      {
        id: 'HOST_INTRO', segmentType: 'host_intro', label: '主持人介紹 + 價值承諾', tag: 'host-intro', layer: 'opening', dur: '約 30 秒',
        content: '嗨大家好，我是你的主持人！歡迎回到我的 Podcast。（停頓）今天這集聽完，你會知道怎麼用最少的工具，做到最大的效率提升。我們開始吧！',
        cues: ['（停頓）', '[BGM 淡出]'],
      },
      {
        id: 'TOPIC_INTRO', segmentType: 'topic_intro', label: '主題引入：AI 工具的現況', tag: 'topic-intro', layer: 'main', dur: '約 2 分鐘',
        content: '先來聊聊背景。（加強語氣）過去一年，AI 工具的數量爆炸性成長，光是生產力工具就超過 500 個。但問題來了——選擇太多，反而讓人不知從何下手。',
        cues: ['（加強語氣）', '（停頓）'],
      },
      {
        id: 'CORE_1', segmentType: 'core_1', label: '核心一：我的 AI 工作流實測', tag: 'core', layer: 'main', dur: '約 8 分鐘',
        content: '先說說我自己的故事。三個月前，我一天花在整理資料上的時間超過兩個小時。但現在，同樣的事情只要 15 分鐘。\n\n（停頓）\n\n這不是魔法，是找到了適合自己的 AI 工作流程。我來一個一個跟你介紹。',
        cues: ['（停頓）', '（加強語氣）'],
      },
      {
        id: 'CORE_2', segmentType: 'core_2', label: '核心二：5 個推薦工具深度介紹', tag: 'core', layer: 'main', dur: '約 10 分鐘',
        content: '好，直接進入正題。第一個工具是 Claude，它是我目前最常用的 AI 助理。\n\n（停頓）\n\n為什麼選 Claude？因為它在理解中文、回覆台灣口語方面表現特別好。接下來第二個工具⋯',
        cues: ['（停頓）'],
      },
      {
        id: 'SUMMARY', segmentType: 'summary', label: '重點摘要', tag: 'summary', layer: 'closing', dur: '約 1 分鐘',
        content: '好，來幫大家快速複習一下。今天介紹了 5 個我每天都在用的 AI 工具，分別是⋯（停頓）記住，重點不是工具多，而是找到適合你的工作流。',
        cues: ['（停頓）'],
      },
      {
        id: 'CTA', segmentType: 'cta', label: '行動呼籲', tag: 'cta', layer: 'closing', dur: '約 20 秒',
        content: '如果今天的內容對你有幫助，請幫我按下訂閱，也歡迎留言告訴我你最想試哪個工具！（加強語氣）你的一個訂閱，就是對我最大的支持。',
        cues: ['（加強語氣）'],
      },
      {
        id: 'PREVIEW', segmentType: 'preview', label: '下集預告', tag: 'preview', layer: 'closing', dur: '約 15 秒',
        content: '下一集，我要跟大家分享一個更進階的主題——怎麼用 AI 自動化你的整個內容產出流程。（停頓）我們下集見！\n\n[片尾音樂]',
        cues: ['（停頓）', '[片尾音樂]'],
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
    canSkipTitleGeneration,
    canSkipScriptGeneration,
  }
})
