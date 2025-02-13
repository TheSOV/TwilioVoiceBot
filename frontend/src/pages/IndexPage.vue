<template>
  <q-page padding>
    <div class="row items-center justify-between q-mb-md">
      <h1 class="text-h4 q-my-none">Voice Bot Dashboard</h1>
      <q-btn
        color="primary"
        icon="person_add"
        label="Manage Users"
        to="/users"
      />
    </div>

    <div class="row q-col-gutter-md">
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="text-h6">Users</div>
          </q-card-section>

          <q-card-section>
            <users-table
              :users="users"
              :loading="loading"
              @call="callUser"
            />
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Call Confirmation Dialog -->
    <q-dialog v-model="showCallDialog">
      <q-card>
        <q-card-section class="row items-center">
          <q-avatar icon="phone" color="primary" text-color="white" />
          <span class="q-ml-sm">Call {{ selectedUser?.name || selectedUser?.phone_number }}?</span>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="primary" v-close-popup />
          <q-btn flat label="Call" color="primary" @click="makeCall" :loading="calling" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useQuasar } from 'quasar'
import { useUsersStore } from 'stores/users'
import UsersTable from 'components/users/UsersTable.vue'
import { api } from 'src/boot/axios'

export default {
  name: 'IndexPage',
  components: {
    UsersTable
  },
  setup() {
    const $q = useQuasar()
    const usersStore = useUsersStore()
    const showCallDialog = ref(false)
    const selectedUser = ref(null)
    const calling = ref(false)

    onMounted(() => {
      usersStore.fetchUsers()
    })

    const callUser = (user) => {
      selectedUser.value = user
      showCallDialog.value = true
    }

    const makeCall = async () => {
      calling.value = true
      try {
        await api.post('/make_call', { 
          phone_number: selectedUser.value.phone_number 
        })
        
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

    return {
      users: computed(() => usersStore.users),
      loading: computed(() => usersStore.loading),
      showCallDialog,
      selectedUser,
      calling,
      callUser,
      makeCall
    }
  }
}
</script>
