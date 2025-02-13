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
          :rows="sortedCallHistory"
          :columns="columns"
          row-key="timestamp"
          :pagination="{ rowsPerPage: 10 }"
          :loading="loading"
        >
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
              {{ formatDate(props.value) }}
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

              <!-- Extracted Info Dialog -->
              <q-btn
                flat
                round
                dense
                color="positive"
                icon="info"
                @click="showExtractedInfo(props.row)"
                :disable="!props.row.extracted_info"
              >
                <q-tooltip>View Extracted Information</q-tooltip>
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

    <!-- Extracted Info Dialog -->
    <q-dialog v-model="showExtractedInfoDialog">
      <q-card style="min-width: 350px">
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6">Extracted Information</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pt-md">
          <q-list>
            <q-item v-for="(value, key) in selectedCall?.extracted_info" :key="key">
              <q-item-section>
                <q-item-label caption>{{ formatFieldName(key) }}</q-item-label>
                <q-item-label>{{ value }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
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
import { defineComponent, ref, computed } from 'vue'
import { date } from 'quasar'
import { useUsersStore } from 'stores/users'

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

  emits: ['update:modelValue'],

  setup(props, { emit }) {
    const usersStore = useUsersStore()
    const show = computed({
      get: () => props.modelValue,
      set: (value) => emit('update:modelValue', value)
    })

    const showTranscriptionDialog = ref(false)
    const showExtractedInfoDialog = ref(false)
    const showAudioDialog = ref(false)
    const selectedCall = ref(null)
    const currentAudioUrl = ref(null)

    const columns = [
      {
        name: 'timestamp',
        required: true,
        label: 'Date & Time',
        align: 'left',
        field: 'timestamp',
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
        name: 'actions',
        label: 'Actions',
        align: 'center',
        field: row => row
      }
    ]

    const sortedCallHistory = computed(() => {
      if (!props.user?.call_history) return []
      return [...props.user.call_history].sort((a, b) => {
        return new Date(b.timestamp) - new Date(a.timestamp)
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

    const formatDate = (timestamp) => {
      return date.formatDate(timestamp, 'YYYY-MM-DD HH:mm:ss')
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

    const showExtractedInfo = (call) => {
      selectedCall.value = call
      showExtractedInfoDialog.value = true
    }

    const refreshUserData = async () => {
      if (props.user?.phone_number) {
        await usersStore.fetchUsers()
      }
    }

    return {
      show,
      columns,
      sortedCallHistory,
      showTranscriptionDialog,
      showExtractedInfoDialog,
      showAudioDialog,
      selectedCall,
      currentAudioUrl,
      getStatusColor,
      formatDuration,
      formatDate,
      formatFieldName,
      playAudio,
      showTranscription,
      showExtractedInfo,
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
</style>
