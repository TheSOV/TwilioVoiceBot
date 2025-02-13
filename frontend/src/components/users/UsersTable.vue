<template>
  <q-table
    :rows="users"
    :columns="columns"
    row-key="phone_number"
    :loading="loading"
  >
    <template v-slot:body-cell-actions="props">
      <q-td :props="props">
        <q-btn-group flat>
          <q-btn
            flat
            round
            color="primary"
            icon="edit"
            @click="$emit('edit', props.row)"
          />
          <q-btn
            flat
            round
            color="negative"
            icon="delete"
            @click="$emit('delete', props.row)"
          />
          <q-btn
            flat
            round
            color="secondary"
            icon="phone"
            @click="$emit('call', props.row)"
          />
        </q-btn-group>
      </q-td>
    </template>
  </q-table>
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'UsersTable',
  props: {
    users: {
      type: Array,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['edit', 'delete', 'call'],
  setup() {
    const columns = [
      {
        name: 'phone_number',
        required: true,
        label: 'Phone Number',
        align: 'left',
        field: 'phone_number',
        sortable: true
      },
      {
        name: 'name',
        label: 'Name',
        align: 'left',
        field: 'name',
        sortable: true
      },
      {
        name: 'comments',
        label: 'Comments',
        align: 'left',
        field: 'comments'
      },
      {
        name: 'actions',
        label: 'Actions',
        align: 'center'
      }
    ]

    return {
      columns
    }
  }
})
</script>
