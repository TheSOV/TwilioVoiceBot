<template>
  <q-dialog v-model="show" maximized @show="refreshUserData">
    <q-card>
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Call History</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-card-section>
        <div class="text-subtitle1 q-mb-md">
          {{ user?.name || user?.phone_number }}
        </div>

        <q-table
          :rows="filteredCalls"
          :columns="columns"
          row-key="timestamp"
          :loading="loading"
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

          <template v-slot:header="props">
            <q-tr :props="props">
              <q-th
                v-for="col in props.cols"
                :key="col.name"
                :props="props"
              >
                {{ col.label }}
              </q-th>
            </q-tr>
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

          <!-- Timestamp column -->
          <template v-slot:body-cell-timestamp="props">
            <q-td :props="props">
              {{ props.value }}
            </q-td>
          </template>

          <!-- Extracted Info column -->
          <template v-slot:body-cell-extracted_info="props">
            <q-td :props="props">
              <div v-if="props.row.extracted_info" class="text-caption">
                <template v-for="(value, key) in props.row.extracted_info" :key="key">
                  <div class="extracted-info-item">
                    <span class="text-weight-medium">{{ formatFieldName(key) }}:</span>
                    <span>{{ value }}</span>
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
      </q-card-section>
    </q-card>

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
  </q-dialog>
</template>

<script>
import { defineComponent, ref, computed, watch } from 'vue'
import { useUsersStore } from 'stores/users'
import { formatDateWithTimezone } from 'src/utils/date'

export default defineComponent({
  name: 'CallHistoryDialog',

  props: {
    modelValue: {
      type: Boolean,
      required: true
    },
    user: {
      type: Object,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    }
  },

  emits: [],

  setup(props, { emit }) {
    const usersStore = useUsersStore()
    const show = computed({
      get: () => props.modelValue,
      set: (value) => emit('update:modelValue', value)
    })

    const showTranscriptionDialog = ref(false)
    const showAudioDialog = ref(false)
    const selectedCall = ref(null)
    const currentAudioUrl = ref(null)

    const filter = ref('')
    const columnFilters = ref({
      timestamp: '',
      call_status: '',
      call_duration: '',
      extracted_info: '',
      actions: ''
    })

    const columns = [
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
        sortable: true
      },
      {
        name: 'extracted_info',
        label: 'Extracted Information',
        align: 'left',
        field: 'extracted_info',
        style: 'width: 300px'
      },
      {
        name: 'actions',
        label: 'Actions',
        align: 'center',
        field: row => row
      }
    ]

    const applyColumnFilters = (row) => {
      return Object.entries(columnFilters.value).every(([key, filterValue]) => {
        if (!filterValue || key === 'actions') return true
        
        const lowercaseFilter = filterValue.toLowerCase()
        let cellValue = row[key]
        
        // Handle date fields
        if (key === 'timestamp' && cellValue) {
          const formattedDate = formatDateWithTimezone(cellValue).toLowerCase()
          return formattedDate.includes(lowercaseFilter)
        }
        
        // Handle extracted info
        if (key === 'extracted_info') {
          return JSON.stringify(cellValue || {}).toLowerCase().includes(lowercaseFilter)
        }
        
        // Handle duration
        if (key === 'call_duration' && cellValue != null) {
          return formatDuration(cellValue).toLowerCase().includes(lowercaseFilter)
        }
        
        // Handle regular fields
        return String(cellValue || '').toLowerCase().includes(lowercaseFilter)
      })
    }

    const filteredCalls = computed(() => {
      if (!props.user?.call_history) return []
      
      const allCalls = [...props.user.call_history].sort((a, b) => {
        return new Date(b.timestamp) - new Date(a.timestamp)
      })
      
      const globalFilter = filter.value.toLowerCase()
      
      return allCalls.filter(call => {
        const matchesColumnFilters = applyColumnFilters(call)
        
        if (!globalFilter) return matchesColumnFilters
        
        const matchesGlobal = 
          formatDateWithTimezone(call.timestamp).toLowerCase().includes(globalFilter) ||
          String(call.call_status || '').toLowerCase().includes(globalFilter) ||
          formatDuration(call.call_duration).toLowerCase().includes(globalFilter) ||
          JSON.stringify(call.extracted_info || {}).toLowerCase().includes(globalFilter)
        
        return matchesColumnFilters && matchesGlobal
      })
    })

    const getStatusColor = (status) => {
      const colors = {
        completed: 'positive',
        failed: 'negative',
        'in-progress': 'warning',
        cancelled: 'grey'
      }
      return colors[status?.toLowerCase()] || 'grey'
    }

    const formatDuration = (duration) => {
      if (!duration) return '-'
      const minutes = Math.floor(duration / 60)
      const seconds = Math.floor(duration % 60)
      return `${minutes}:${seconds.toString().padStart(2, '0')}`
    }

    const formatFieldName = (key) => {
      return key.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ')
    }

    const playAudio = (audioFileName) => {
      if (!audioFileName) return
      
      // Extract the filename from the full path
      const filename = audioFileName.split('/').pop()
      
      // Create URL using the mounted recordings directory
      currentAudioUrl.value = `/recordings/combined/${encodeURIComponent(filename)}`
      showAudioDialog.value = true
    }

    const showTranscription = (call) => {
      selectedCall.value = call
      showTranscriptionDialog.value = true
    }

    const refreshUserData = async () => {
      if (props.user?.phone_number) {
        await usersStore.fetchUsers()
      }
    }

    const clearFilters = () => {
      filter.value = ''
      Object.keys(columnFilters.value).forEach(key => {
        columnFilters.value[key] = ''
      })
    }

    watch(() => props.modelValue, (newVal) => {
      if (newVal) {
        clearFilters()
      }
    })

    return {
      show,
      filter,
      columns,
      columnFilters,
      filteredCalls,
      selectedCall,
      showTranscriptionDialog,
      showAudioDialog,
      currentAudioUrl,
      getStatusColor,
      formatDuration,
      formatFieldName,
      playAudio,
      showTranscription,
      clearFilters,
      refreshUserData
    }
  }
})
</script>

<style scoped>
.conversation-text {
  font-family: monospace;
  line-height: 1.5;
}

.extracted-info-item {
  margin-bottom: 2px;
  display: flex;
  gap: 4px;
}

.extracted-info-item:last-child {
  margin-bottom: 0;
}

.q-table th {
  white-space: normal;
  padding: 8px 16px;
}
</style>
