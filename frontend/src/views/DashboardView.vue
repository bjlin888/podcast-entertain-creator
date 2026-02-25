<template>
  <div>
    <DashHero @new-episode="handleNew" />
    <div class="dash-main">
      <StatsRow :total="store.totalCount" :done="store.doneCount" :draft="store.draftCount" />

      <SectionToolbar
        v-model:searchQuery="store.searchQuery"
        v-model:sortBy="store.sortBy"
        v-model:filter="store.filter"
      />

      <!-- Episode grid -->
      <div class="ep-grid">
        <template v-if="store.filteredEpisodes.length">
          <EpisodeCard
            v-for="(ep, i) in store.filteredEpisodes"
            :key="ep.id"
            :episode="ep"
            :index="store.getEpisodeIndex(ep.id)"
            @open="goToFlow(ep)"
            @continue="goToFlow(ep)"
            @delete="confirmDelete(ep)"
            @publish="openPublish(ep)"
          />
        </template>

        <!-- Empty state -->
        <div v-else-if="!store.episodes.length" class="empty-wrap">
          <span class="ei">🎙️</span>
          <h3>還沒有任何集數</h3>
          <p>按下上方按鈕開始建立你的第一集 Podcast 腳本！</p>
          <button class="btn-primary empty-cta" @click="handleNew">
            ＋ 建立第一集
          </button>
        </div>

        <!-- No results -->
        <div v-else class="no-results">
          <span class="ni">🔍</span>
          <p>找不到符合的集數，試試調整搜尋或篩選條件。</p>
        </div>
      </div>
    </div>

    <DeleteModal
      :visible="deleteTarget !== null"
      :title="deleteTarget?.title || ''"
      @close="deleteTarget = null"
      @confirm="doDelete"
    />

    <PublishModal
      :visible="publishTarget !== null"
      :episode-title="publishTarget?.title || ''"
      @close="publishTarget = null"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useEpisodesStore } from '../stores/episodes'
import DashHero from '../components/dashboard/DashHero.vue'
import StatsRow from '../components/dashboard/StatsRow.vue'
import SectionToolbar from '../components/dashboard/SectionToolbar.vue'
import EpisodeCard from '../components/dashboard/EpisodeCard.vue'
import DeleteModal from '../components/modals/DeleteModal.vue'
import PublishModal from '../components/modals/PublishModal.vue'

const router = useRouter()
const store = useEpisodesStore()

const deleteTarget = ref(null)
const publishTarget = ref(null)

onMounted(() => {
  store.fetchEpisodes()
  window.addEventListener('keydown', onKey)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
})

function onKey(e) {
  if (e.key === 'n' || e.key === 'N') {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
    e.preventDefault()
    handleNew()
  }
}

async function handleNew() {
  const ep = await store.createEpisode()
  if (ep) {
    router.push(`/flow/${ep.id}`)
  }
}

function goToFlow(ep) {
  router.push(`/flow/${ep.id}`)
}

function confirmDelete(ep) {
  deleteTarget.value = ep
}

async function doDelete() {
  if (deleteTarget.value) {
    await store.deleteEpisode(deleteTarget.value.id)
    deleteTarget.value = null
  }
}

function openPublish(ep) {
  publishTarget.value = ep
}
</script>

<style scoped>
.ep-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(278px, 1fr));
  gap: 18px;
}
.empty-cta {
  width: auto;
  display: inline-flex;
  padding: 14px 28px;
}
</style>
