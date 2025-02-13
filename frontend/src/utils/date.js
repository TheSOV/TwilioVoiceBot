// Format a UTC ISO string to local timezone
export const formatToLocalTime = (utcIsoString) => {
  if (!utcIsoString) return '-'

  try {
    // Parse the UTC ISO string
    const utcDate = new Date(utcIsoString)
    
    // Format in local timezone without specifying timeZone (browser will convert automatically)
    const localFormatted = utcDate.toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })

    return localFormatted
  } catch (error) {
    console.error('Error formatting date:', error)
    return '-'
  }
}

// Format the date with timezone info
export const formatDateWithTimezone = (utcIsoString) => {
  if (!utcIsoString) return '-'
  
  try {
    return formatToLocalTime(utcIsoString)
  } catch (error) {
    console.error('Error formatting date with timezone:', error)
    return '-'
  }
}
