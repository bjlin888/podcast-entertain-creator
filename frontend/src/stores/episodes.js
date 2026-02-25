import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useApi } from '../composables/useApi'

const COVERS = [
  { grad: 'linear-gradient(135deg, #F4631E, #FF8A50)', emoji: '🎯' },
  { grad: 'linear-gradient(135deg, #1A8F8A, #24A89F)', emoji: '🌊' },
  { grad: 'linear-gradient(135deg, #6B48FF, #A78BFA)', emoji: '✨' },
  { grad: 'linear-gradient(135deg, #D4A017, #F6D860)', emoji: '⚡' },
  { grad: 'linear-gradient(135deg, #E53E8A, #F472B6)', emoji: '🎵' },
  { grad: 'linear-gradient(135deg, #2D6A4F, #52B788)', emoji: '🌿' },
]

const STEP_LABELS = ['', '填寫主題', '挑選標題', '審閱腳本', '給意見', '已完成']

export { COVERS, STEP_LABELS }

export const useEpisodesStore = defineStore('episodes', () => {
  const episodes = ref([])
  const filter = ref('all')
  const searchQuery = ref('')
  const sortBy = ref('newest')
  const isLoading = ref(false)

  // Computed
  const totalCount = computed(() => episodes.value.length)
  const doneCount = computed(() => episodes.value.filter(e => e.status === 'done').length)
  const draftCount = computed(() => episodes.value.filter(e => e.status === 'draft').length)

  const filteredEpisodes = computed(() => {
    let list = [...episodes.value]

    // Filter by status
    if (filter.value === 'done') list = list.filter(e => e.status === 'done')
    if (filter.value === 'draft') list = list.filter(e => e.status === 'draft')

    // Filter by search
    const q = searchQuery.value.toLowerCase().trim()
    if (q) {
      list = list.filter(e =>
        (e.title || '').toLowerCase().includes(q) ||
        (e.topic || '').toLowerCase().includes(q) ||
        (e.style || '').toLowerCase().includes(q)
      )
    }

    // Sort
    if (sortBy.value === 'newest') list.sort((a, b) => (b.date || '').localeCompare(a.date || ''))
    if (sortBy.value === 'oldest') list.sort((a, b) => (a.date || '').localeCompare(b.date || ''))
    if (sortBy.value === 'done') list.sort((a, b) => (a.status === 'done' ? -1 : 1))
    if (sortBy.value === 'draft') list.sort((a, b) => (a.status === 'draft' ? -1 : 1))

    return list
  })

  // Helper
  function getCover(index) {
    return COVERS[index % COVERS.length]
  }

  function getStepLabel(step) {
    return STEP_LABELS[step] || ''
  }

  function getEpisodeIndex(id) {
    return episodes.value.findIndex(e => e.id === id)
  }

  // Actions
  async function fetchEpisodes() {
    const api = useApi()
    isLoading.value = true
    try {
      const data = await api.get('/api/v1/projects')
      episodes.value = (data.projects || []).map((p, i) => mapProjectToEpisode(p, i))
    } catch (err) {
      // If API not available, keep existing data or empty
      if (!episodes.value.length) {
        episodes.value = []
      }
    } finally {
      isLoading.value = false
    }
  }

  function mapProjectToEpisode(project, fallbackIndex) {
    const step = computeStep(project)
    const progress = computeProgress(step)
    return {
      id: project.project_id || project.id,
      title: project.selected_title || project.topic || '(untitled)',
      topic: project.topic || '',
      style: project.style || '輕鬆聊天',
      dur: project.duration_min ? `${project.duration_min} 分鐘` : '30 分鐘',
      audience: project.audience || '',
      hostCount: project.host_count === 2 ? '雙人對談' : project.host_count >= 3 ? '多人' : '我一人',
      status: step >= 5 ? 'done' : 'draft',
      progress,
      step,
      date: project.created_at ? project.created_at.slice(0, 10) : new Date().toISOString().slice(0, 10),
      ci: fallbackIndex % COVERS.length,
      titles: project.titles || [],
      selTitle: project.selected_title_index ?? -1,
      segments: project.segments || [],
    }
  }

  function computeStep(project) {
    if (project.status === 'done' || project.step === 5) return 5
    if (project.step) return project.step
    if (project.segments && project.segments.length) return 3
    if (project.titles && project.titles.length) return 2
    return 1
  }

  function computeProgress(step) {
    const map = { 1: 5, 2: 30, 3: 60, 4: 80, 5: 100 }
    return map[step] || 0
  }

  async function createEpisode() {
    const api = useApi()
    try {
      const data = await api.post('/api/v1/projects', {})
      const ci = Math.floor(Math.random() * COVERS.length)
      const ep = {
        id: data.project?.project_id || data.project_id || 'ep_' + Date.now(),
        title: '(新集數)',
        topic: '',
        style: '輕鬆聊天',
        dur: '30 分鐘',
        audience: '',
        hostCount: '我一人',
        status: 'draft',
        progress: 0,
        step: 1,
        date: new Date().toISOString().slice(0, 10),
        ci,
        titles: [],
        selTitle: -1,
        segments: [],
      }
      episodes.value.unshift(ep)
      return ep
    } catch {
      // Offline fallback
      const ci = Math.floor(Math.random() * COVERS.length)
      const ep = {
        id: 'ep_' + Date.now(),
        title: '(新集數)',
        topic: '',
        style: '輕鬆聊天',
        dur: '30 分鐘',
        audience: '',
        hostCount: '我一人',
        status: 'draft',
        progress: 0,
        step: 1,
        date: new Date().toISOString().slice(0, 10),
        ci,
        titles: [],
        selTitle: -1,
        segments: [],
      }
      episodes.value.unshift(ep)
      return ep
    }
  }

  async function deleteEpisode(id) {
    const api = useApi()
    try {
      await api.del(`/api/v1/projects/${id}`)
    } catch {
      // Continue with local delete
    }
    episodes.value = episodes.value.filter(e => e.id !== id)
  }

  function updateEpisode(id, updates) {
    const idx = episodes.value.findIndex(e => e.id === id)
    if (idx !== -1) {
      episodes.value[idx] = { ...episodes.value[idx], ...updates }
    }
  }

  function getEpisode(id) {
    return episodes.value.find(e => e.id === id)
  }

  return {
    episodes,
    filter,
    searchQuery,
    sortBy,
    isLoading,
    totalCount,
    doneCount,
    draftCount,
    filteredEpisodes,
    getCover,
    getStepLabel,
    getEpisodeIndex,
    fetchEpisodes,
    createEpisode,
    deleteEpisode,
    updateEpisode,
    getEpisode,
  }
})
