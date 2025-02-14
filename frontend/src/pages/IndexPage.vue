<template>
  <q-page padding class="full-width">
    <div class="row items-center justify-between q-mb-md">
      <h1 class="text-h4 q-my-none">Clients</h1>
      <div class="row q-gutter-sm">
        <!-- Import Users Button -->
        <q-btn
          color="secondary"
          icon="upload_file"
          label="Import Clients"
          @click="showImportDialog = true"
        />
        
        <!-- Export Users Button -->
        <q-btn
          color="secondary"
          icon="download"
          label="Export Clients"
          @click="showExportDialog = true"
        />
        
        <!-- Add Client Button -->
        <q-btn
          color="primary"
          icon="add"
          label="Add Client"
          @click="showAddDialog = true"
        />
      </div>
    </div>

    <!-- Import Users Dialog -->
    <q-dialog v-model="showImportDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Import Users</div>
          <div class="text-caption q-mt-sm">
            Supported formats:
            <ul>
              <li>Excel/CSV: First column = phone number, second column (optional) = name</li>
              <li>TXT: Comma-separated phone numbers</li>
            </ul>
          </div>
        </q-card-section>

        <q-card-section>
          <q-file 
            v-model="importFile" 
            label="Select File" 
            accept=".xlsx,.xls,.csv,.txt"
            outlined
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="primary" v-close-popup />
          <q-btn 
            label="Import" 
            color="primary" 
            @click="importUsers"
            :disable="!importFile"
          />
        </q-card-actions>

        <!-- Failed Users Details -->
        <q-card-section v-if="importFailedUsers && importFailedUsers.length > 0">
          <q-expansion-item
            expand-separator
            label="Failed Imports"
            :caption="`${importFailedUsers.length} entries could not be imported`"
          >
            <q-list>
              <q-item 
                v-for="(failedUser, index) in importFailedUsers" 
                :key="index"
                clickable
              >
                <q-item-section>
                  <q-item-label>
                    Row {{ failedUser.row }}: {{ failedUser.input }}
                  </q-item-label>
                  <q-item-label caption>
                    Error: {{ failedUser.error }}
                  </q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-expansion-item>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Export Users Dialog -->
    <q-dialog v-model="showExportDialog">
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">Export Users</div>
        </q-card-section>

        <q-card-section>
          <q-select 
            v-model="exportFormat" 
            :options="['xlsx', 'csv', 'txt']"
            label="Export Format"
            outlined
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="primary" v-close-popup />
          <q-btn 
            label="Export" 
            color="primary" 
            @click="exportUsers"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <users-table
      :users="users"
      :loading="loading"
      @edit="editUser"
      @delete="confirmDelete"
      @call="makeCall"
      @bulk-delete="confirmBulkDelete"
      ref="usersTableRef"
      class="full-width"
    />

    <!-- Add/Edit Dialog -->
    <q-dialog v-model="showAddDialog">
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">{{ editMode ? 'Edit Client' : 'Add Client' }}</div>
        </q-card-section>

        <q-card-section>
          <user-form
            :initial-data="selectedUser"
            :edit-mode="editMode"
            @submit="onSubmit"
            @cancel="closeDialog"
          />
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Delete Confirmation Dialog -->
    <q-dialog v-model="showDeleteDialog">
      <q-card>
        <q-card-section class="row items-center">
          <q-avatar icon="warning" color="negative" text-color="white" />
          <span class="q-ml-sm">
            {{ bulkDeleteUsers ? 
              `Are you sure you want to delete ${bulkDeleteUsers.length} selected clients?` :
              'Are you sure you want to delete this client?'
            }}
          </span>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="primary" v-close-popup />
          <q-btn flat label="Delete" color="negative" @click="deleteUser" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Call Confirmation Dialog -->
    <q-dialog 
      v-model="showCallDialog" 
      v-bind="callDialogProps"
      class="call-dialog"
    >
      <q-card 
        :class="{ 'calling-card': calling }"
        style="min-width: 350px;"
      >
        <q-card-section class="row items-center">
          <q-avatar icon="phone" color="primary" text-color="white" />
          <span class="q-ml-sm">Confirm call to {{ selectedUser?.name || selectedUser?.phone_number }}?</span>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn 
            flat 
            label="Cancel" 
            color="primary" 
            v-close-popup 
            :disable="calling"
          />
          <q-btn 
            :loading="calling"
            flat 
            label="Call" 
            color="positive" 
            @click="confirmCall"
            :disable="calling"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useQuasar } from 'quasar'
import { useUsersStore } from 'stores/users'
import { api } from 'src/boot/axios'
import UserForm from 'components/users/UserForm.vue'
import UsersTable from 'components/users/UsersTable.vue'

export default {
  name: 'UsersPage',
  components: {
    UserForm,
    UsersTable
  },
  setup() {
    const $q = useQuasar()
    const usersStore = useUsersStore()
    const showAddDialog = ref(false)
    const showDeleteDialog = ref(false)
    const showCallDialog = ref(false)
    const showImportDialog = ref(false)
    const showExportDialog = ref(false)
    const selectedUser = ref(null)
    const bulkDeleteUsers = ref(null)
    const editMode = ref(false)
    const calling = ref(false)
    const usersTableRef = ref(null)
    const importFile = ref(null)
    const exportFormat = ref('xlsx')
    const importFailedUsers = ref([])

    const closeDialog = () => {
      showAddDialog.value = false
      showCallDialog.value = false
      selectedUser.value = null
      bulkDeleteUsers.value = null
      editMode.value = false
    }

    const editUser = (user) => {
      selectedUser.value = { ...user }
      editMode.value = true
      showAddDialog.value = true
    }

    const confirmDelete = (user) => {
      selectedUser.value = user
      bulkDeleteUsers.value = null
      showDeleteDialog.value = true
    }

    const confirmBulkDelete = (users) => {
      bulkDeleteUsers.value = users
      selectedUser.value = null
      showDeleteDialog.value = true
    }

    const deleteUser = async () => {
      try {
        if (bulkDeleteUsers.value) {
          // Handle bulk delete
          for (const user of bulkDeleteUsers.value) {
            await usersStore.deleteUser(user.phone_number)
          }
          $q.notify({
            type: 'positive',
            message: `${bulkDeleteUsers.value.length} clients deleted successfully`
          })
          // Clear selections only after successful deletion
          if (usersTableRef.value) {
            usersTableRef.value.selected = []
          }
        } else {
          // Handle single delete
          await usersStore.deleteUser(selectedUser.value.phone_number)
          $q.notify({
            type: 'positive',
            message: 'Client deleted successfully'
          })
        }
        showDeleteDialog.value = false
        selectedUser.value = null
        bulkDeleteUsers.value = null
      } catch (err) {
        console.error('Delete error:', err)
        $q.notify({
          type: 'negative',
          message: `Failed to delete client(s): ${err.message}`
        })
      }
    }

    const makeCall = (user) => {
      selectedUser.value = user
      showCallDialog.value = true
    }

    const confirmCall = async () => {
      calling.value = true
      try {
        // Make the call and get the result
        const callResponse = await api.post('/make_call', { 
          phone_number: selectedUser.value.phone_number 
        })
        
        // Record the call result
        await usersStore.recordCall(
          selectedUser.value.phone_number, 
          callResponse.data
        )
        
        $q.notify({
          type: 'positive',
          message: `Call to ${selectedUser.value.name || selectedUser.value.phone_number} completed successfully`
        })
        
        showCallDialog.value = false
      } catch (err) {
        console.error('Call error:', err)
        $q.notify({
          type: 'negative',
          message: `Failed to make call: ${err.message}`
        })
      } finally {
        calling.value = false
        selectedUser.value = null
      }
    }

    const callDialogProps = computed(() => ({
      persistent: true, // Always prevent closing
      seamless: false, // Ensure full background is maintained
      'no-click-outside': true // Prevent closing when clicking outside
    }))

    const onSubmit = async (formData) => {
      try {
        if (editMode.value) {
          await usersStore.updateUser(selectedUser.value.phone_number, formData)
          $q.notify({
            type: 'positive',
            message: 'Client updated successfully'
          })
        } else {
          await usersStore.createUser(formData)
          $q.notify({
            type: 'positive',
            message: 'Client added successfully'
          })
        }
        
        closeDialog()
      } catch (err) {
        console.error('Submit error:', err)
        $q.notify({
          type: 'negative',
          message: `${editMode.value ? 'Failed to update' : 'Failed to add'} client: ${err.message}`
        })
      }
    }

    const importUsers = async () => {
      if (!importFile.value) {
        $q.notify({
          type: 'negative',
          message: 'Please select a file to import'
        })
        return
      }

      const formData = new FormData()
      formData.append('file', importFile.value)

      try {
        const response = await api.post('/api/users/import', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        // Refresh users list
        await usersStore.fetchUsers()

        // Store failed users for display
        importFailedUsers.value = response.data.failed_users || []

        $q.notify({
          type: 'positive',
          message: `Imported ${response.data.imported_count} users`,
          caption: response.data.failed_count > 0 
            ? `${response.data.failed_count} users failed to import` 
            : ''
        })

        // If there are failed imports, keep the dialog open
        if (response.data.failed_count > 0) {
          return
        }

        // Clear file selector and close dialog
        importFile.value = null
        showImportDialog.value = false
      } catch (error) {
        $q.notify({
          type: 'negative',
          message: 'Failed to import users',
          caption: error.response?.data?.detail || error.message
        })
      }
    }

    const exportUsers = async () => {
      try {
        const response = await api.post('/api/users/export', null, {
          params: { format: exportFormat.value },
          responseType: 'blob'
        })

        // Create a link and trigger download
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `users_export.${exportFormat.value}`)
        document.body.appendChild(link)
        link.click()
        link.remove()

        showExportDialog.value = false
      } catch (error) {
        $q.notify({
          type: 'negative',
          message: 'Failed to export users',
          caption: error.response?.data?.detail || error.message
        })
      }
    }

    onMounted(() => {
      usersStore.fetchUsers()
    })

    return {
      users: computed(() => usersStore.users),
      loading: computed(() => usersStore.loading),
      showAddDialog,
      showDeleteDialog,
      showCallDialog,
      showImportDialog,
      showExportDialog,
      selectedUser,
      bulkDeleteUsers,
      editMode,
      calling,
      callDialogProps,
      closeDialog,
      editUser,
      confirmDelete,
      confirmBulkDelete,
      deleteUser,
      makeCall,
      confirmCall,
      onSubmit,
      usersTableRef,
      importFile,
      exportFormat,
      importFailedUsers,
      importUsers,
      exportUsers
    }
  }
}
</script>

<style scoped>
.q-page {
  width: 100%;
  max-width: 100%;
}

.full-width {
  width: 100%;
  max-width: 100%;
}

.call-dialog {
  background-color: #fff;
}
.calling-card {
  background-color: #fff;
}
</style>
