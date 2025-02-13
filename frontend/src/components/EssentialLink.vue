<template>
  <q-item
    clickable
    :to="isInternalLink ? props.link : undefined"
    :href="!isInternalLink ? props.link : undefined"
    :target="!isInternalLink ? '_blank' : undefined"
  >
    <q-item-section
      v-if="props.icon"
      avatar
    >
      <q-icon :name="props.icon" />
    </q-item-section>

    <q-item-section>
      <q-item-label>{{ props.title }}</q-item-label>
      <q-item-label caption>{{ props.caption }}</q-item-label>
    </q-item-section>
  </q-item>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },

  caption: {
    type: String,
    default: ''
  },

  link: {
    type: String,
    default: '#'
  },

  icon: {
    type: String,
    default: ''
  }
})

const isInternalLink = computed(() => {
  // Check if link is relative (starts with /) or is root path
  return props.link.startsWith('/') || props.link === ''
})
</script>
