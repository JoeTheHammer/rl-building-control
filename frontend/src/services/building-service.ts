// src/services/building-service.ts
import axios from 'axios'

const API_BASE = 'http://127.0.0.1:8000/api/building'

export const fetchBuildingModels = async (): Promise<string[]> => {
  const response = await axios.get<{ files: string[] }>(`${API_BASE}/all`)
  return response.data.files
}
