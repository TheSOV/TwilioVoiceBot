<template>
  <q-page padding class="full-width">
    <div class="row items-center justify-between q-mb-md">
      <h1 class="text-h4 q-my-none">Call History</h1>
    </div>

    <call-history-filter />
    <call-history-table />
  </q-page>
</template>

<script>
import { defineComponent, onMounted } from 'vue'
import { useCallHistoryStore } from 'src/stores/call_history'
import CallHistoryFilter from 'components/call_history/CallHistoryFilter.vue'
import CallHistoryTable from 'components/call_history/CallHistoryTable.vue'

export default defineComponent({
  name: 'CallHistoryPage',
  components: {
    CallHistoryFilter,
    CallHistoryTable
  },
  setup() {
    const callHistoryStore = useCallHistoryStore()

    onMounted(() => {
      // Fetch initial call histories
      callHistoryStore.fetchCallHistories()
    })

    return {}
  }
})
</script>

<style scoped>
.full-width {
  width: 100%;
  max-width: 100%;
}
</style>
