import axios from 'axios'

const client = axios.create({ baseURL: '/api/ev-insight' })

export function scoreBatteryHealth(readingsFile, vehiclesFile) {
  const form = new FormData()
  form.append('readings', readingsFile)
  if (vehiclesFile) form.append('vehicles', vehiclesFile)
  return client.post('/health-score', form)
}

export function getEvInsightHealth() {
  return client.get('/health')
}
