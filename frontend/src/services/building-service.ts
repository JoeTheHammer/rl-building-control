// src/services/building-service.ts
import axios from 'axios'
import { getBaseHost } from '@/services/api-service.ts'

const API_BASE = `${getBaseHost()}:8000/api/building`

export const fetchBuildingModels = async (): Promise<string[]> => {
  const response = await axios.get<{ files: string[] }>(`${API_BASE}/all`)
  return response.data.files
}
