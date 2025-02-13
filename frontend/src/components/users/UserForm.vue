<template>
  <q-form @submit="onSubmit" class="q-gutter-md">
    <q-input
      v-model="form.phone_number"
      label="Phone Number"
      :rules="[val => !!val || 'Phone number is required']"
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
import { ref, onMounted } from 'vue'

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

    onMounted(() => {
      if (props.initialData) {
        form.value = { ...props.initialData }
      }
    })

    const onSubmit = async () => {
      loading.value = true
      try {
        emit('submit', { ...form.value })
      } finally {
        loading.value = false
      }
    }

    return {
      form,
      loading,
      onSubmit
    }
  }
}
</script>
