<template>
  <q-page padding>
    <div class="row items-center justify-between q-mb-md">
      <h1 class="text-h4 q-my-none">Clients</h1>
      <q-btn
        color="primary"
        icon="add"
        label="Add Client"
        @click="showAddDialog = true"
      />
    </div>

    <users-table
      :users="users"
      :loading="loading"
      @edit="editUser"
      @delete="confirmDelete"
      @call="makeCall"
      @bulk-delete="confirmBulkDelete"
      ref="usersTableRef"
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
    const selectedUser = ref(null)
    const bulkDeleteUsers = ref(null)
    const editMode = ref(false)
    const calling = ref(false)
    const usersTableRef = ref(null)

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

    onMounted(() => {
      usersStore.fetchUsers()
    })

    return {
      users: computed(() => usersStore.users),
      loading: computed(() => usersStore.loading),
      showAddDialog,
      showDeleteDialog,
      showCallDialog,
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
      usersTableRef
    }
  }
}
</script>

<style scoped>
.q-page {
  max-width: 1200px;
  margin: 0 auto;
}
.call-dialog {
  background-color: #fff;
}
.calling-card {
  background-color: #fff;
}
</style>
