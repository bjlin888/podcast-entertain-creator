<template>
  <div class="flow-main">
    <FlowProgress :percent="flow.progressPercent" />

    <StepTopic v-if="flow.currentStep === 1" />
    <StepTitles v-else-if="flow.currentStep === 2" />
    <StepScript
      v-else-if="flow.currentStep === 3"
      @edit="openEditModal"
      @voice="openVoiceModal"
    />
    <StepFeedback v-else-if="flow.currentStep === 4" @satisfied="flow.goToExport()" />
    <StepExport
      v-else-if="flow.currentStep === 5"
      @back-to-list="router.push('/')"
      @new-episode="handleNewEpisode"
    />

    <BottomBar
      :current-step="flow.currentStep"
      :can-proceed="flow.canProceed"
      @back="handleBack"
      @next="handleNext"
    />

    <LoadingOverlay
      :visible="flow.isLoading"
      :text="flow.loadingText"
      :sub-text="flow.loadingSub"
    />

    <VoiceModal
      :visible="voiceModalVisible"
      :segment-index="voiceSegIndex"
      :host-count="parseHostCount(flow.hostCount)"
      @close="voiceModalVisible = false"
      @generate="handleVoiceGenerate"
      @generate-multi="handleMultiSpeakerGenerate"
    />

    <EditModal
      :visible="editModalVisible"
      :segment-label="editSegLabel"
      :content="editSegContent"
      @close="editModalVisible = false"
      @save="handleEditSave"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useFlowStore } from '../stores/flow'
import { useEpisodesStore } from '../stores/episodes'
import FlowProgress from '../components/flow/FlowProgress.vue'
import StepTopic from '../components/flow/StepTopic.vue'
import StepTitles from '../components/flow/StepTitles.vue'
import StepScript from '../components/flow/StepScript.vue'
import StepFeedback from '../components/flow/StepFeedback.vue'
import StepExport from '../components/flow/StepExport.vue'
import BottomBar from '../components/BottomBar.vue'
import LoadingOverlay from '../components/LoadingOverlay.vue'
import VoiceModal from '../components/modals/VoiceModal.vue'
import EditModal from '../components/modals/EditModal.vue'

const props = defineProps({
  id: { type: String, required: true },
})

const router = useRouter()
const route = useRoute()
const flow = useFlowStore()
const episodes = useEpisodesStore()

// Modal state
const voiceModalVisible = ref(false)
const voiceSegIndex = ref(0)
const editModalVisible = ref(false)
const editSegIndex = ref(0)
const editSegLabel = ref('')
const editSegContent = ref('')

onMounted(() => {
  loadEpisode()
  window.addEventListener('keydown', onKey)
})

onUnmounted(() => {
  flow.saveToEpisodeStore()
  window.removeEventListener('keydown', onKey)
})

watch(() => route.params.id, () => {
  loadEpisode()
})

async function loadEpisode() {
  try {
    await flow.fetchAndLoad(props.id)
  } catch {
    // Fallback: load from episodes store (offline mode)
    const ep = episodes.getEpisode(props.id)
    if (ep) flow.loadEpisode(ep)
  }
}

function onKey(e) {
  if (e.key === 'Escape') {
    voiceModalVisible.value = false
    editModalVisible.value = false
    return
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    if (flow.canProceed && flow.currentStep <= 3) {
      e.preventDefault()
      handleNext()
    }
  }
}

function handleBack() {
  if (flow.currentStep > 1) {
    flow.currentStep--
    flow.saveToEpisodeStore()
  }
}

async function handleNext() {
  switch (flow.currentStep) {
    case 1:
      await flow.generateTitles()
      break
    case 2:
      await flow.generateScript()
      break
    case 3:
      flow.currentStep = 4
      flow.saveToEpisodeStore()
      break
  }
}

function openEditModal(segIndex) {
  const seg = flow.segments[segIndex]
  if (!seg) return
  editSegIndex.value = segIndex
  editSegLabel.value = seg.label || seg.id || ''
  editSegContent.value = seg.content || ''
  editModalVisible.value = true
}

function openVoiceModal(segIndex) {
  voiceSegIndex.value = segIndex
  voiceModalVisible.value = true
}

async function handleEditSave(newContent) {
  await flow.updateSegment(editSegIndex.value, newContent)
  editModalVisible.value = false
}

async function handleVoiceGenerate({ segmentIndex, voice, speed, pitch, ttsProvider, stylePrompt }) {
  flow.voiceConfig = {
    voice,
    speed,
    pitch,
    ttsProvider: ttsProvider || 'gemini',
    stylePrompt: stylePrompt || '',
    speakers: flow.voiceConfig.speakers,
  }
  voiceModalVisible.value = false
  await flow.generateTTS(segmentIndex)
}

async function handleMultiSpeakerGenerate(config) {
  voiceModalVisible.value = false
  await flow.generateMultiSpeakerTTS(config)
}

function parseHostCount(hc) {
  if (hc === '我一人') return 1
  if (hc === '雙人對談') return 2
  return 3
}

async function handleNewEpisode() {
  const ep = await episodes.createEpisode()
  if (ep) {
    router.push(`/flow/${ep.id}`)
  }
}
</script>
