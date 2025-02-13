<template>
  <div class="call-history-filter">
    <div class="row q-col-gutter-md">
      <div class="col-12 col-md-3">
        <q-input
          v-model="localFilters.phoneNumber"
          label="Phone Number"
          dense
          clearable
          @update:model-value="applyFilters"
        />
      </div>
      <div class="col-12 col-md-3">
        <q-select
          v-model="localFilters.callStatus"
          :options="callStatusOptions"
          label="Call Status"
          dense
          clearable
          @update:model-value="applyFilters"
        />
      </div>
      <div class="col-12 col-md-3">
        <q-input
          v-model="localFilters.extractedInfoKeyword"
          label="Extracted Info Keyword"
          dense
          clearable
          @update:model-value="applyFilters"
        />
      </div>
      <div class="col-12 col-md-3">
        <div class="row q-col-gutter-sm">
          <div class="col-6">
            <q-input
              v-model="localFilters.startDate"
              label="Start Date"
              type="date"
              dense
              clearable
              @update:model-value="applyFilters"
            />
          </div>
          <div class="col-6">
            <q-input
              v-model="localFilters.endDate"
              label="End Date"
              type="date"
              dense
              clearable
              @update:model-value="applyFilters"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, watch } from 'vue'
import { useCallHistoryStore } from 'src/stores/call_history'

export default defineComponent({
  name: 'CallHistoryFilter',
  setup() {
    const callHistoryStore = useCallHistoryStore()

    const localFilters = ref({
      phoneNumber: '',
      callStatus: null,
      extractedInfoKeyword: '',
      startDate: null,
      endDate: null
    })

    const callStatusOptions = [
      'completed', 
      'failed', 
      'in-progress', 
      'canceled'
    ]

    const applyFilters = () => {
      // Update store filters
      Object.keys(localFilters.value).forEach(key => {
        callHistoryStore.setFilter(key, localFilters.value[key])
      })

      // Trigger fetch
      callHistoryStore.fetchCallHistories()
    }

    // Watch for external filter changes
    watch(() => callHistoryStore.filters, (newFilters) => {
      localFilters.value = { ...newFilters }
    }, { immediate: true })

    return {
      localFilters,
      callStatusOptions,
      applyFilters
    }
  }
})
</script>

<style scoped>
.call-history-filter {
  margin-bottom: 20px;
}
</style>
