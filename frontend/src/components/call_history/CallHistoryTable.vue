<template>
  <div>
    <q-table
      :rows="callHistories"
      :columns="columns"
      :loading="loading"
      row-key="timestamp"
      class="full-width"
      selection="multiple"
      v-model:selected="selected"
    >
      <!-- Top row slot for global filter -->
      <template v-slot:top>
        <div class="row full-width q-gutter-sm">
          <q-input
            dense
            debounce="300"
            v-model="filter"
            placeholder="Global search"
            class="col-grow"
            clearable
          >
            <template v-slot:append>
              <q-icon name="search" />
            </template>
          </q-input>
          
          <!-- Export Button -->
          <q-btn
            color="primary"
            icon="download"
            label="Export Selected"
            :disable="!selected.length"
            @click="exportToExcel"
          />
        </div>
        <div class="row full-width q-gutter-sm q-mt-sm">
          <div v-for="col in columns.filter(c => c.name !== 'actions')" :key="col.name" class="col">
            <q-input 
              dense
              debounce="300"
              v-model="columnFilters[col.name]"
              :placeholder="`Filter ${col.label}`"
              clearable
            >
              <template v-slot:append>
                <q-icon name="filter_alt" size="xs" />
              </template>
            </q-input>
          </div>
        </div>
      </template>

      <!-- Status column -->
      <template v-slot:body-cell-call_status="props">
        <q-td :props="props">
          <q-chip
            :color="getStatusColor(props.value)"
            text-color="white"
            dense
            class="q-px-sm"
          >
            {{ props.value }}
          </q-chip>
        </q-td>
      </template>

      <!-- Duration column -->
      <template v-slot:body-cell-call_duration="props">
        <q-td :props="props">
          {{ formatDuration(props.value) }}
        </q-td>
      </template>

      <!-- Extracted Info column -->
      <template v-slot:body-cell-extracted_info="props">
        <q-td :props="props">
          <div v-if="props.row.extracted_info" class="text-caption">
            <template v-for="(value, key) in props.row.extracted_info" :key="key">
              <div class="extracted-info-item">
                <span class="text-weight-medium">{{ formatFieldName(key) }}:</span>
                <span class="q-ml-xs">{{ value }}</span>
              </div>
            </template>
          </div>
          <span v-else class="text-grey">No information extracted</span>
        </q-td>
      </template>

      <!-- Actions column -->
      <template v-slot:body-cell-actions="props">
        <q-td :props="props" class="q-gutter-sm">
          <!-- Audio Player -->
          <q-btn
            flat
            round
            dense
            color="primary"
            icon="play_arrow"
            @click="playAudio(props.row.audio_file_name)"
            :disable="!props.row.audio_file_name"
          >
            <q-tooltip>Play Recording</q-tooltip>
          </q-btn>

          <!-- Transcription Dialog -->
          <q-btn
            flat
            round
            dense
            color="info"
            icon="chat"
            @click="showTranscription(props.row)"
            :disable="!props.row.conversation"
          >
            <q-tooltip>View Transcription</q-tooltip>
          </q-btn>
        </q-td>
      </template>
    </q-table>

    <!-- Transcription Dialog -->
    <q-dialog v-model="showTranscriptionDialog">
      <q-card style="min-width: 350px; max-width: 600px">
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6">Call Transcription</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pt-md">
          <div class="conversation-text" style="white-space: pre-line">
            {{ selectedCall?.conversation }}
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Audio Player Dialog -->
    <q-dialog v-model="showAudioDialog">
      <q-card style="min-width: 350px">
        <q-card-section class="row items-center">
          <div class="text-h6">Call Recording</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pt-none">
          <audio
            v-if="currentAudioUrl"
            controls
            class="full-width"
            :src="currentAudioUrl"
          >
            Your browser does not support the audio element.
          </audio>
        </q-card-section>
      </q-card>
    </q-dialog>
  </div>
</template>

<script>
import { defineComponent, ref, computed } from 'vue'
import { useCallHistoryStore } from 'src/stores/call_history'
import { formatDateWithTimezone } from 'src/utils/date'

export default defineComponent({
  name: 'CallHistoryTable',
  setup() {
    const callHistoryStore = useCallHistoryStore()

    const columns = [
      {
        name: 'phone_number',
        required: true,
        label: 'Phone Number',
        align: 'left',
        field: 'phone_number',
        sortable: true
      },
      {
        name: 'timestamp',
        required: true,
        label: 'Date & Time',
        align: 'left',
        field: 'timestamp',
        format: val => formatDateWithTimezone(val),
        sortable: true
      },
      {
        name: 'call_status',
        required: true,
        label: 'Status',
        align: 'left',
        field: 'call_status',
        sortable: true
      },
      {
        name: 'call_duration',
        label: 'Duration',
        align: 'left',
        field: 'call_duration',
        format: val => parseInt(val),
        sortable: true
      },
      {
        name: 'extracted_info',
        label: 'Extracted Info',
        align: 'left',
        field: 'extracted_info',
        sortable: false
      },
      {
        name: 'actions',
        label: 'Actions',
        align: 'center',
        field: 'actions',
        sortable: false
      }
    ]

    // Filtering
    const filter = ref('')
    const columnFilters = ref({})

    const filteredCallHistories = computed(() => {
      let result = callHistoryStore.callHistories

      // Global filter
      if (filter.value) {
        const lowercaseFilter = filter.value.toLowerCase()
        result = result.filter(call => 
          Object.values(call).some(val => 
            String(val).toLowerCase().includes(lowercaseFilter)
          )
        )
      }

      // Column filters
      Object.keys(columnFilters.value).forEach(key => {
        const filterValue = columnFilters.value[key]
        if (filterValue) {
          const lowercaseFilter = filterValue.toLowerCase()
          result = result.filter(call => 
            String(call[key]).toLowerCase().includes(lowercaseFilter)
          )
        }
      })

      return result
    })

    // Selection and export
    const selected = ref([])

    const exportToExcel = async () => {
      try {
        // Get the data to export
        const dataToExport = selected.value.length ? selected.value : filteredCallHistories.value
        
        // Call the export API
        const response = await fetch('/api/call_histories/export', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ calls: dataToExport }),
        })
        
        if (!response.ok) {
          throw new Error('Export failed')
        }
        
        // Get the file blob
        const blob = await response.blob()
        
        // Create download link
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `call_history_${new Date().toISOString().split('T')[0]}.xlsx`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } catch (error) {
        console.error('Export failed:', error)
        // You might want to show an error notification here
      }
    }

    // Dialogs and audio
    const showTranscriptionDialog = ref(false)
    const showAudioDialog = ref(false)
    const selectedCall = ref(null)
    const currentAudioUrl = ref(null)

    const showTranscription = (call) => {
      selectedCall.value = call
      showTranscriptionDialog.value = true
    }

    const playAudio = (audioFileName) => {
      if (!audioFileName) return
      
      // Extract the filename from the full path
      const filename = audioFileName.split('/').pop()
      
      // Create URL using the mounted recordings directory
      currentAudioUrl.value = `/recordings/combined/${encodeURIComponent(filename)}`
      
      // Open audio dialog
      showAudioDialog.value = true
    }

    // Utility functions
    const getStatusColor = (status) => {
      const colors = {
        completed: 'positive',
        failed: 'negative',
        'in-progress': 'warning',
        canceled: 'grey'
      }
      return colors[status?.toLowerCase()] || 'grey'
    }

    const formatDuration = (duration) => {
      // Check for null, undefined, NaN, or non-numeric values
      if (duration == null || isNaN(duration) || typeof duration !== 'number') return '-'
      
      // Ensure duration is a positive number
      const totalSeconds = Math.max(0, Math.round(duration))
      
      const hours = Math.floor(totalSeconds / 3600)
      const minutes = Math.floor((totalSeconds % 3600) / 60)
      const seconds = totalSeconds % 60
      
      if (hours > 0) {
        return `${hours}h ${minutes}m ${seconds}s`
      } else if (minutes > 0) {
        return `${minutes}m ${seconds}s`
      } else {
        return `${seconds}s`
      }
    }

    const formatFieldName = (key) => {
      return key.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ')
    }

    return {
      callHistories: filteredCallHistories,
      loading: computed(() => callHistoryStore.loading),
      columns,
      
      // Filtering
      filter,
      columnFilters,

      // Selection and export
      selected,
      exportToExcel,

      // Dialogs and interactions
      showTranscriptionDialog,
      showAudioDialog,
      selectedCall,
      currentAudioUrl,
      
      // Methods
      showTranscription,
      playAudio,
      getStatusColor,
      formatDuration,
      formatFieldName,
      formatDateWithTimezone
    }
  }
})
</script>

<style scoped>
.conversation-text {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: monospace;
  background-color: #f4f4f4;
  padding: 10px;
  border-radius: 4px;
}

.extracted-info-item {
  display: flex;
  align-items: baseline;
  margin-bottom: 2px;
}

.extracted-info-item:last-child {
  margin-bottom: 0;
}
</style>