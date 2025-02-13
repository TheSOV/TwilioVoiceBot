<template>
  <div>
    <!-- Users Table Section -->
    <div class="q-mb-md">
      <div class="row q-mb-md">
        <q-btn 
          color="negative" 
          icon="delete" 
          label="Delete Selected" 
          @click="onDeleteSelected"
          :disable="selected.length === 0"
          class="q-mr-sm"
        />
        <q-btn 
          color="primary" 
          icon="add" 
          label="Add to Call List" 
          @click="addSelectedToCallList"
          :disable="selected.length === 0"
          class="q-mr-sm"
        />
      </div>

      <q-table
        :rows="users"
        :columns="columns"
        row-key="phone_number"
        :loading="loading"
        selection="multiple"
        v-model:selected="selected"
      >
        <template v-slot:body-cell-actions="props">
          <q-td :props="props" class="q-gutter-sm">
            <q-btn
              flat
              round
              dense
              color="info"
              icon="history"
              @click="showCallHistory(props.row)"
              :disable="!props.row.call_history?.length"
            >
              <q-tooltip>View Call History</q-tooltip>
            </q-btn>
            <q-btn
              flat
              round
              dense
              color="primary"
              icon="phone"
              @click="$emit('call', props.row)"
            >
              <q-tooltip>Call Client</q-tooltip>
            </q-btn>
            <q-btn
              flat
              round
              dense
              color="warning"
              icon="edit"
              @click="$emit('edit', props.row)"
            >
              <q-tooltip>Edit Client</q-tooltip>
            </q-btn>
            <q-btn
              flat
              round
              dense
              color="negative"
              icon="delete"
              @click="$emit('delete', props.row)"
            >
              <q-tooltip>Delete Client</q-tooltip>
            </q-btn>
          </q-td>
        </template>
      </q-table>
    </div>

    <!-- Call List Section -->
    <div>
      <div class="row q-mb-md items-center">
        <div class="text-h6 q-mr-md">Call List</div>
        <q-btn 
          color="negative" 
          icon="clear" 
          label="Clear List" 
          @click="callListStore.clearCallList()"
          :disable="callList.length === 0"
          class="q-mr-sm"
        />
        <q-btn 
          color="negative" 
          icon="delete" 
          label="Delete Selected" 
          @click="removeSelectedFromCallList"
          :disable="selectedCallListUsers.length === 0"
          class="q-mr-sm"
        />
        <q-btn 
          color="primary" 
          icon="phone" 
          label="Call All" 
          @click="callAllInList"
          :disable="callList.length === 0 || calling"
          :loading="calling"
        />
      </div>

      <q-table
        :rows="callList"
        :columns="columns"
        row-key="phone_number"
        selection="multiple"
        v-model:selected="selectedCallListUsers"
      >
        <template v-slot:body-cell-actions="props">
          <q-td :props="props">
            <q-btn-group flat>
              <q-btn
                flat
                round
                color="negative"
                icon="delete"
                @click="removeFromCallList(props.row)"
              />
              <q-btn
                flat
                round
                color="secondary"
                icon="phone"
                @click="$emit('call', props.row)"
              />
            </q-btn-group>
          </q-td>
        </template>
        <template v-slot:no-data>
          <div class="full-width row flex-center text-grey q-gutter-sm q-pa-md">
            <q-icon size="2em" name="list" />
            <span>No clients in call list</span>
          </div>
        </template>
      </q-table>
    </div>

    <!-- Calling Dialog -->
    <q-dialog persistent v-model="callListStore.calling">
      <q-card style="min-width: 350px">
        <q-card-section class="row items-center">
          <q-avatar icon="phone" color="primary" text-color="white" />
          <span class="q-ml-md" v-if="callListStore.currentUser">
            Calling {{ callListStore.currentUser.name || callListStore.currentUser.phone_number }}
            ({{ callListStore.currentCallIndex + 1 }} of {{ callList.length }})
          </span>
          <span class="q-ml-md" v-else>
            Initializing calls...
          </span>
        </q-card-section>

        <q-card-section>
          <q-linear-progress
            :value="callList.length ? (callListStore.currentCallIndex + 1) / callList.length : 0"
            color="primary"
            class="q-mt-md"
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            flat
            label="Cancel Remaining"
            color="negative"
            @click="callListStore.cancelCalls()"
            :disable="callListStore.shouldCancelCalls"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Call History Dialog -->
    <call-history-dialog
      v-model="showCallHistoryDialog"
      :user="selectedUser"
      :loading="false"
    />
  </div>
</template>

<script>
import { defineComponent, ref, computed } from 'vue'
import { useQuasar } from 'quasar'
import { useCallListStore } from 'src/stores/call_list'
import CallHistoryDialog from './CallHistoryDialog.vue'

export default defineComponent({
  name: 'UsersTable',
  components: {
    CallHistoryDialog
  },
  props: {
    users: {
      type: Array,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['edit', 'delete', 'call', 'bulk-delete'],
  setup(props, { emit }) {
    const $q = useQuasar()
    const callListStore = useCallListStore()
    
    const selected = ref([])
    const selectedCallListUsers = ref([])
    const showCallHistoryDialog = ref(false)
    const selectedUser = ref(null)

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
        name: 'name',
        label: 'Name',
        align: 'left',
        field: 'name',
        sortable: true
      },
      {
        name: 'comments',
        label: 'Comments',
        align: 'left',
        field: 'comments'
      },
      {
        name: 'last_called_at',
        label: 'Last Called',
        align: 'left',
        field: 'last_called_at',
        format: (val) => formatLastCalledDate(val)
      },
      {
        name: 'actions',
        label: 'Actions',
        align: 'center'
      }
    ]

    const formatLastCalledDate = (dateValue) => {
      if (!dateValue) return 'Never'
      
      const date = new Date(dateValue)
      const formatter = new Intl.RelativeTimeFormat(undefined, {
        numeric: 'auto',
        style: 'long'
      })
      
      const now = new Date()
      const diffInSeconds = (now.getTime() - date.getTime()) / 1000
      
      const intervals = [
        { seconds: 60, divisor: 1, unit: 'second' },
        { seconds: 3600, divisor: 60, unit: 'minute' },
        { seconds: 86400, divisor: 3600, unit: 'hour' },
        { seconds: 2592000, divisor: 86400, unit: 'day' },
        { seconds: 31536000, divisor: 2592000, unit: 'month' },
        { seconds: Infinity, divisor: 31536000, unit: 'year' }
      ]
      
      const interval = intervals.find(i => diffInSeconds < i.seconds)
      
      if (interval) {
        const value = Math.floor(diffInSeconds / interval.divisor)
        return formatter.format(-value, interval.unit)
      }
      
      return date.toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short'
      })
    }

    const onDeleteSelected = () => {
      emit('bulk-delete', selected.value)
    }

    const addSelectedToCallList = () => {
      callListStore.addToCallList(selected.value)
      selected.value = [] // Clear selection after adding to call list
    }

    const removeFromCallList = (user) => {
      callListStore.removeFromCallList(user)
    }

    const removeSelectedFromCallList = () => {
      callListStore.removeSelectedFromCallList(selectedCallListUsers.value)
      selectedCallListUsers.value = []
    }

    const callAllInList = async () => {
      try {
        await callListStore.callAllInList()
        $q.notify({
          type: 'positive',
          message: 'All calls completed successfully'
        })
      } catch (err) {
        $q.notify({
          type: 'negative',
          message: `Failed to complete calls: ${err.message}`
        })
      }
    }

    const showCallHistory = (user) => {
      selectedUser.value = user
      showCallHistoryDialog.value = true
    }

    return {
      columns,
      selected,
      selectedCallListUsers,
      showCallHistoryDialog,
      selectedUser,
      callList: computed(() => callListStore.callList),
      calling: computed(() => callListStore.calling),
      callListStore,
      formatLastCalledDate,
      onDeleteSelected,
      addSelectedToCallList,
      removeFromCallList,
      removeSelectedFromCallList,
      callAllInList,
      showCallHistory
    }
  }
})
</script>

<style scoped>
.q-table__bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>