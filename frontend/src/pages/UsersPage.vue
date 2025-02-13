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
      @call="callUser"
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
          <span class="q-ml-sm">Are you sure you want to delete this user?</span>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="primary" v-close-popup />
          <q-btn flat label="Delete" color="negative" @click="deleteUser" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useQuasar } from 'quasar'
import { useUsersStore } from 'stores/users'
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
    const selectedUser = ref(null)
    const editMode = ref(false)

    const closeDialog = () => {
      showAddDialog.value = false
      selectedUser.value = null
      editMode.value = false
    }

    const editUser = (user) => {
      selectedUser.value = { ...user }
      editMode.value = true
      showAddDialog.value = true
    }

    const confirmDelete = (user) => {
      selectedUser.value = user
      showDeleteDialog.value = true
    }

    const deleteUser = async () => {
      try {
        await usersStore.deleteUser(selectedUser.value.phone_number)
        showDeleteDialog.value = false
        selectedUser.value = null
        $q.notify({
          type: 'positive',
          message: 'User deleted successfully'
        })
      } catch (err) {
        console.error('Delete error:', err)
        $q.notify({
          type: 'negative',
          message: `Failed to delete user: ${err.message}`
        })
      }
    }

    const onSubmit = async (formData) => {
      try {
        if (editMode.value) {
          await usersStore.updateUser(selectedUser.value.phone_number, formData)
          $q.notify({
            type: 'positive',
            message: 'User updated successfully'
          })
        } else {
          await usersStore.createUser(formData)
          $q.notify({
            type: 'positive',
            message: 'User created successfully'
          })
        }
        closeDialog()
      } catch (err) {
        console.error('Submit error:', err)
        $q.notify({
          type: 'negative',
          message: `${editMode.value ? 'Failed to update' : 'Failed to create'} user: ${err.message}`
        })
        closeDialog()
      }
    }

    const callUser = (user) => {
      $q.notify({
        type: 'info',
        message: `To call ${user.name || user.phone_number}, please use the main page`
      })
    }

    onMounted(() => {
      usersStore.fetchUsers()
    })

    return {
      users: computed(() => usersStore.users),
      loading: computed(() => usersStore.loading),
      showAddDialog,
      showDeleteDialog,
      selectedUser,
      editMode,
      editUser,
      confirmDelete,
      deleteUser,
      onSubmit,
      closeDialog,
      callUser
    }
  }
}
</script>
