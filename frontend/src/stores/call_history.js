import { defineStore } from 'pinia'
import { api } from 'src/boot/axios'

export const useCallHistoryStore = defineStore('callHistory', {
  state: () => ({
    callHistories: [],
    loading: false,
    error: null,
    filters: {
      startDate: null,
      endDate: null,
      phoneNumber: '',
      callStatus: '',
      extractedInfoKeyword: ''
    }
  }),

  actions: {
    async fetchCallHistories() {
      this.loading = true
      this.error = null

      try {
        const response = await api.get('/api/call_histories', {
          params: {
            start_date: this.filters.startDate,
            end_date: this.filters.endDate,
            phone_number: this.filters.phoneNumber,
            call_status: this.filters.callStatus,
            extracted_info_keyword: this.filters.extractedInfoKeyword
          }
        })
        this.callHistories = response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch call histories'
        console.error('Error fetching call histories:', error)
      } finally {
        this.loading = false
      }
    },

    setFilter(key, value) {
      this.filters[key] = value
    },

    clearFilters() {
      this.filters = {
        startDate: null,
        endDate: null,
        phoneNumber: '',
        callStatus: '',
        extractedInfoKeyword: ''
      }
    }
  }
})
