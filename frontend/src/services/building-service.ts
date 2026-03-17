// src/services/building-service.ts
import axios from 'axios'
import { getApiBase } from '@/services/api-service.ts'

const API_BASE = getApiBase('/api/building')

export const fetchBuildingModels = async (): Promise<string[]> => {
  const response = await axios.get<{ files: string[] }>(`${API_BASE}/all`)
  return response.data.files
}
