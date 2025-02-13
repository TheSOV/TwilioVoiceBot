import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from 'src/boot/axios'
import { useUsersStore } from 'src/stores/users'

export const useCallListStore = defineStore('callList', () => {
  const callList = ref([])
  const calling = ref(false)
  const currentCallIndex = ref(0)
  const shouldCancelCalls = ref(false)
  const currentUser = ref(null)
  const usersStore = useUsersStore()

  const uniqueCallList = computed(() => {
    const seen = new Set()
    return callList.value.filter(user => {
      const duplicate = seen.has(user.phone_number)
      seen.add(user.phone_number)
      return !duplicate
    })
  })

  function addToCallList(users) {
    const usersArray = Array.isArray(users) ? users : [users]
    usersArray.forEach(user => {
      if (!callList.value.some(u => u.phone_number === user.phone_number)) {
        callList.value.push(user)
      }
    })
  }

  function removeFromCallList(user) {
    callList.value = callList.value.filter(u => u.phone_number !== user.phone_number)
  }

  function removeSelectedFromCallList(selectedUsers) {
    const selectedArray = Array.isArray(selectedUsers) ? selectedUsers : [selectedUsers]
    callList.value = callList.value.filter(
      user => !selectedArray.some(selected => selected.phone_number === user.phone_number)
    )
  }

  async function callAllInList() {
    calling.value = true
    currentCallIndex.value = 0
    shouldCancelCalls.value = false
    const users = uniqueCallList.value

    try {
      for (const [index, user] of users.entries()) {
        if (shouldCancelCalls.value) {
          break
        }
        
        currentCallIndex.value = index
        currentUser.value = user

        // Make the call
        const callResponse = await api.post('/make_call', { 
          phone_number: user.phone_number 
        })

        // Record the call result
        await usersStore.recordCall(
          user.phone_number,
          callResponse.data
        )

        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    } catch (err) {
      console.error('Failed to complete calls:', err)
      throw err
    } finally {
      calling.value = false
      currentUser.value = null
      currentCallIndex.value = 0
      shouldCancelCalls.value = false
    }
  }

  function cancelCalls() {
    shouldCancelCalls.value = true
  }

  function clearCallList() {
    callList.value = []
  }

  return {
    callList: uniqueCallList,
    calling,
    currentCallIndex,
    currentUser,
    shouldCancelCalls,
    addToCallList,
    removeFromCallList,
    removeSelectedFromCallList,
    callAllInList,
    cancelCalls,
    clearCallList
  }
})
