import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000
})

export const generateTripPlan = async (data) => {
  const res = await api.post('/plan', data)
  return res.data
}
