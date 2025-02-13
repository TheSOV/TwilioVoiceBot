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
        :rows="filteredUsers"
        :columns="columns"
        row-key="phone_number"
        :loading="loading"
        selection="multiple"
        v-model:selected="selected"
        :filter="filter"
      >
        <template v-slot:top>
          <div class="row full-width q-gutter-sm">
            <q-input
              dense
              debounce="300"
              v-model="filter"
              placeholder="Global search"
              class="col-grow"
            >
              <template v-slot:append>
                <q-icon name="search" />
              </template>
            </q-input>
          </div>
          <div class="row full-width q-gutter-sm q-mt-sm">
            <div v-for="col in columns" :key="col.name" :class="col.name === 'select' || col.name === 'actions' ? 'col-auto' : 'col'">
              <q-input 
                v-if="col.filterable"
                dense
                debounce="300"
                v-model="columnFilters[col.name]"
                :placeholder="`Filter ${col.label}`"
                clearable
                @input="applyColumnFilters"
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
              :style="getColumnStyle(col.name)"
            >
              <template v-if="col.name === 'select'">
                <q-checkbox v-model="props.selected" />
              </template>
              <template v-else>
                {{ col.label }}
              </template>
            </q-th>
          </q-tr>
        </template>

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
import { formatDateWithTimezone } from 'src/utils/date'

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
    const filter = ref('')
    const columnFilters = ref({
      select: '',  
      name: '',
      phone_number: '',
      created_at: '',
      last_call: '',
      actions: ''  
    })

    const columns = [
      {
        name: 'select',
        label: '',
        field: 'select',
        sortable: false,
        filterable: false
      },
      {
        name: 'name',
        required: true,
        label: 'Name',
        align: 'left',
        field: 'name',
        format: val => val || '-',
        sortable: true,
        filterable: true
      },
      {
        name: 'phone_number',
        required: true,
        label: 'Phone',
        align: 'left',
        field: 'phone_number',
        sortable: true,
        filterable: true
      },
      {
        name: 'created_at',
        label: 'Added On',
        align: 'left',
        field: 'created_at',
        format: val => formatDateWithTimezone(val),
        sortable: true,
        filterable: true
      },
      {
        name: 'last_call',
        label: 'Last Call',
        align: 'left',
        field: (user) => user.call_history?.[0]?.timestamp || null,
        format: val => val ? formatDateWithTimezone(val) : 'Never',
        sortable: true,
        filterable: true
      },
      {
        name: 'actions',
        label: 'Actions',
        align: 'center',
        sortable: false,
        filterable: false
      }
    ]

    const getColumnStyle = (columnName) => {
      if (columnName === 'actions') {
        return 'width: 150px'
      }
      return ''
    }

    const applyColumnFilters = () => {
      const hasActiveFilters = Object.values(columnFilters.value).some(filter => filter && filter.trim() !== '')
      
      if (!hasActiveFilters && !filter.value) {
        return () => true
      }

      return (user) => {
        return Object.entries(columnFilters.value).every(([key, filterValue]) => {
          // Skip non-filterable columns and empty filters
          const column = columns.find(col => col.name === key)
          if (!column?.filterable || !filterValue || filterValue.trim() === '') return true
          
          const lowercaseFilter = filterValue.toLowerCase()
          let cellValue = user[key]
          
          if (key === 'last_call') {
            cellValue = user.call_history?.[0]?.timestamp
          }
          
          // Handle date fields
          if (key === 'created_at' || key === 'last_call') {
            if (cellValue) {
              const formattedDate = formatDateWithTimezone(cellValue).toLowerCase()
              return formattedDate.includes(lowercaseFilter)
            }
            return false
          }
          
          // Handle regular fields
          return String(cellValue || '').toLowerCase().includes(lowercaseFilter)
        })
      }
    }

    const filteredUsers = computed(() => {
      const allUsers = props.users
      const filterFn = applyColumnFilters()
      const globalFilter = filter.value.toLowerCase()
      
      return allUsers.filter(user => {
        return filterFn(user) && (
          !globalFilter || 
          user.name.toLowerCase().includes(globalFilter) ||
          user.phone_number.toLowerCase().includes(globalFilter) ||
          formatDateWithTimezone(user.created_at).toLowerCase().includes(globalFilter) ||
          (user.call_history?.[0]?.timestamp && formatDateWithTimezone(user.call_history?.[0]?.timestamp).toLowerCase().includes(globalFilter))
        )
      })
    })

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
      filter,
      columnFilters,
      callList: computed(() => callListStore.callList),
      calling: computed(() => callListStore.calling),
      callListStore,
      filteredUsers,
      onDeleteSelected,
      addSelectedToCallList,
      removeFromCallList,
      removeSelectedFromCallList,
      callAllInList,
      showCallHistory,
      getColumnStyle
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

.q-table th {
  white-space: normal;
  padding: 8px 16px;
}
</style>