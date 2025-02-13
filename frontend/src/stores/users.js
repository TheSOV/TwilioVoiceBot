import { defineStore } from 'pinia'
import { api } from 'src/boot/axios'

export const useUsersStore = defineStore('users', {
  state: () => ({
    users: [],
    loading: false,
    error: null
  }),

  actions: {
    async fetchUsers() {
      this.loading = true
      try {
        const response = await api.get('/api/users')
        this.users = response.data
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },

    async createUser(userData) {
      try {
        const response = await api.post('/api/users', userData)
        this.users.push(response.data)
        return response.data
      } catch (error) {
        this.error = error.message
        throw error
      }
    },

    async updateUser(phoneNumber, userData) {
      try {
        const response = await api.put(`/api/users/${phoneNumber}`, userData)
        const index = this.users.findIndex(u => u.phone_number === phoneNumber)
        if (index !== -1) {
          this.users[index] = response.data
        }
        return response.data
      } catch (error) {
        this.error = error.message
        throw error
      }
    },

    async deleteUser(phoneNumber) {
      try {
        await api.delete(`/api/users/${phoneNumber}`)
        this.users = this.users.filter(u => u.phone_number !== phoneNumber)
      } catch (error) {
        this.error = error.message
        throw error
      }
    }
  }
})
