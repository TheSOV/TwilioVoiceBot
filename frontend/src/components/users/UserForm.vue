<template>
  <q-form @submit="onSubmit" class="q-gutter-md">
    <q-input
      v-model="form.phone_number"
      label="Phone Number"
      :hint="phoneNumberCountry ? `Country: ${phoneNumberCountry}` : ''"
      :rules="[
        val => !!val || 'Phone number is required',
        val => validatePhoneNumber(val) || 'Invalid phone number'
      ]"
    />
    <q-input
      v-model="form.name"
      label="Name"
    />
    <q-input
      v-model="form.comments"
      type="textarea"
      label="Comments"
    />
    <div class="row justify-end q-gutter-sm">
      <q-btn
        flat
        label="Cancel"
        color="grey"
        @click="$emit('cancel')"
      />
      <q-btn
        :loading="loading"
        type="submit"
        color="primary"
        :label="editMode ? 'Update' : 'Create'"
      />
    </div>
  </q-form>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { parsePhoneNumberWithError, isValidPhoneNumber } from 'libphonenumber-js'

export default {
  name: 'UserForm',
  props: {
    initialData: {
      type: Object,
      default: () => ({})
    },
    editMode: {
      type: Boolean,
      default: false
    }
  },
  emits: ['submit', 'cancel'],
  setup(props, { emit }) {
    const loading = ref(false)
    const form = ref({
      phone_number: '',
      name: '',
      comments: ''
    })
    
    const phoneNumberCountry = computed(() => {
      try {
        // Remove any non-digit characters except '+'
        const cleanNumber = form.value.phone_number.replace(/[^\d+]/g, '')
        
        // If number starts with 0, prepend +34 for Spanish numbers
        let formattedNumber = cleanNumber
        if (formattedNumber.startsWith('0')) {
          formattedNumber = `+34${formattedNumber.slice(1)}`
        } else if (!formattedNumber.startsWith('+')) {
          // If no country code, assume Spanish number
          formattedNumber = `+34${formattedNumber}`
        }

        const phoneNumber = parsePhoneNumberWithError(formattedNumber)
        
        // Get country name
        if (phoneNumber && phoneNumber.country) {
          // Mapping of country codes to full names
          const countryNames = {
            'ES': 'Spain',
            'GB': 'United Kingdom',
            'US': 'United States',
            'FR': 'France',
            'DE': 'Germany',
            'IT': 'Italy',
            'PT': 'Portugal',
            // Add more countries as needed
          }
          
          return countryNames[phoneNumber.country] || phoneNumber.country
        }
        return null
      } catch {
        return null
      }
    })

    const validatePhoneNumber = (number) => {
      // Remove any non-digit characters except '+'
      const cleanNumber = number.replace(/[^\d+]/g, '')
      
      // If number starts with 0, prepend +34 for Spanish numbers
      let formattedNumber = cleanNumber
      if (formattedNumber.startsWith('0')) {
        formattedNumber = `+34${formattedNumber.slice(1)}`
      } else if (!formattedNumber.startsWith('+')) {
        // If no country code, assume Spanish number
        formattedNumber = `+34${formattedNumber}`
      }

      try {
        const phoneNumber = parsePhoneNumberWithError(formattedNumber)
        return phoneNumber && isValidPhoneNumber(formattedNumber)
      } catch {
        return false
      }
    }

    onMounted(() => {
      if (props.initialData) {
        form.value = { ...props.initialData }
      }
    })

    const onSubmit = async () => {
      loading.value = true
      try {
        // Normalize phone number before submission
        const cleanNumber = form.value.phone_number.replace(/[^\d+]/g, '')
        let formattedNumber = cleanNumber
        
        if (formattedNumber.startsWith('0')) {
          formattedNumber = `+34${formattedNumber.slice(1)}`
        } else if (!formattedNumber.startsWith('+')) {
          formattedNumber = `+34${formattedNumber}`
        }
        
        form.value.phone_number = formattedNumber
        
        emit('submit', { ...form.value })
      } finally {
        loading.value = false
      }
    }

    return {
      form,
      loading,
      phoneNumberCountry,
      onSubmit,
      validatePhoneNumber
    }
  }
}
</script>
