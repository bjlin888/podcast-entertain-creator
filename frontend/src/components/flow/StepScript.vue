<template>
  <div class="step-script anim-rise">
    <div class="step-icon anim-bobble">📄</div>
    <h1 class="step-h1">你的完整腳本來了！</h1>

    <div class="tip-box">
      <span>💡</span>
      <span>點開段落查看內容，可以修改文字或試聽示範語音。滿意後按下方繼續。</span>
    </div>

    <div class="seg-list">
      <SegmentCard
        v-for="(seg, i) in flow.segments"
        :key="seg.id || i"
        :segment="seg"
        :index="i"
        :is-open="openIndex === i"
        @toggle="toggleSeg(i)"
        @edit="$emit('edit', i)"
        @voice="$emit('voice', i)"
        @upload="handleUpload"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useFlowStore } from '../../stores/flow'
import SegmentCard from './SegmentCard.vue'

const flow = useFlowStore()

defineEmits(['edit', 'voice'])

const openIndex = ref(0)

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
  gap: 11px;
}
</style>
