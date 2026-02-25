<template>
  <div class="step-script anim-rise">
    <div class="step-icon anim-bobble">📄</div>
    <h1 class="step-h1">你的完整腳本來了！</h1>

    <div class="tip-box">
      <span>💡</span>
      <span>點開段落查看內容，可以修改文字或試聽示範語音。滿意後按下方繼續。</span>
    </div>

    <div class="seg-list">
      <template v-for="group in layerGroups" :key="group.key">
        <div class="layer-group">
          <div class="layer-header" :class="group.key">
            <span class="layer-label">{{ group.title }}</span>
            <span class="layer-count">{{ group.segments.length }} 段</span>
          </div>
          <div class="layer-segments">
            <SegmentCard
              v-for="seg in group.segments"
              :key="seg.id || seg._index"
              :segment="seg"
              :index="seg._index"
              :is-open="openIndex === seg._index"
              @toggle="toggleSeg(seg._index)"
              @edit="$emit('edit', seg._index)"
              @voice="$emit('voice', seg._index)"
              @upload="handleUpload"
            />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useFlowStore } from '../../stores/flow'
import SegmentCard from './SegmentCard.vue'

const flow = useFlowStore()

defineEmits(['edit', 'voice'])

const openIndex = ref(0)

const LAYER_TITLES = {
  opening: '第一層：開場',
  main: '第二層：主體內容',
  closing: '第三層：收尾',
}

const layerGroups = computed(() => {
  const groups = { opening: [], main: [], closing: [] }
  flow.segments.forEach((seg, i) => {
    const enriched = { ...seg, _index: i }
    const layer = seg.layer || 'main'
    if (groups[layer]) {
      groups[layer].push(enriched)
    } else {
      groups.main.push(enriched)
    }
  })
  return ['opening', 'main', 'closing']
    .filter(key => groups[key].length > 0)
    .map(key => ({
      key,
      title: LAYER_TITLES[key],
      segments: groups[key],
    }))
})

function toggleSeg(i) {
  openIndex.value = openIndex.value === i ? -1 : i
}

async function handleUpload({ index, file }) {
  await flow.uploadHostAudio(index, file)
}
</script>

<style scoped>
.step-script {
  text-align: center;
}
.step-icon {
  font-size: 56px;
  margin-bottom: 10px;
}
.step-h1 {
  font-family: var(--font-display);
  font-size: 30px;
  font-weight: 700;
  margin-bottom: 18px;
}
.tip-box {
  text-align: left;
}
.seg-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.layer-group {
  text-align: left;
}
.layer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  border-radius: var(--radius-xs);
  margin-bottom: 8px;
}
.layer-header.opening {
  background: var(--gold-pale);
  border-left: 4px solid var(--gold);
}
.layer-header.main {
  background: var(--teal-pale);
  border-left: 4px solid var(--teal);
}
.layer-header.closing {
  background: var(--orange-pale);
  border-left: 4px solid var(--orange);
}
.layer-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
}
.layer-count {
  font-size: 12px;
  color: var(--gray-mid);
}
.layer-segments {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-left: 12px;
  border-left: 2px solid var(--gray-light);
  margin-left: 6px;
}
</style>
