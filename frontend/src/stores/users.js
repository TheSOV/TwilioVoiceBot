import { defineStore } from 'pinia'
import { api } from 'src/boot/axios'

export const useUsersStore = defineStore('users', {
  state: () => ({
    users: [],
    loading: false
  }),

  actions: {
    async fetchUsers() {
      this.loading = true
      try {
        const response = await api.get('/api/users')
        this.users = response.data.map(user => ({
          ...user,
          last_called_at: user.last_called_at ? new Date(user.last_called_at) : null,
          call_history: user.call_history || []
        }))
      } catch (error) {
        console.error('Failed to fetch users:', error)
        this.users = []
      } finally {
        this.loading = false
      }
    },

    async createUser(userData) {
      try {
        const response = await api.post('/api/users', userData)
        this.users.push({
          ...response.data,
          last_called_at: null,
          call_history: []
        })
        return response.data
      } catch (error) {
        console.error('Failed to create user:', error)
        // Transform the error to include the server's error message
        if (error.response?.data?.detail) {
          throw new Error(error.response.data.detail)
        } else if (error.response?.data) {
          throw new Error(
            typeof error.response.data === 'string' 
              ? error.response.data 
              : JSON.stringify(error.response.data)
          )
        }
        throw error
      }
    },

    async updateUser(phoneNumber, userData) {
      try {
        const response = await api.put(`/api/users/${phoneNumber}`, userData)
        const index = this.users.findIndex(u => u.phone_number === phoneNumber)
        if (index !== -1) {
          this.users[index] = {
            ...response.data,
            last_called_at: this.users[index].last_called_at,
            call_history: this.users[index].call_history
          }
        }
        return response.data
      } catch (error) {
        console.error('Failed to update user:', error)
        throw error
      }
    },

    async deleteUser(phoneNumber) {
      try {
        await api.delete(`/api/users/${phoneNumber}`)
        this.users = this.users.filter(u => u.phone_number !== phoneNumber)
      } catch (error) {
        console.error('Failed to delete user:', error)
        throw error
      }
    },

    async recordCall(phoneNumber, callResult) {
      try {
        const response = await api.post(`/api/users/${phoneNumber}/calls`, callResult)
        const index = this.users.findIndex(u => u.phone_number === phoneNumber)
        if (index !== -1) {
          // Update last called time and call history
          this.users[index].last_called_at = new Date()
          this.users[index].call_history = [
            ...(this.users[index].call_history || []),
            { 
              timestamp: new Date(), 
              ...callResult 
            }
          ]
        }
        return response.data
      } catch (error) {
        console.error('Failed to record call:', error)
        throw error
      }
    }
  }
})
