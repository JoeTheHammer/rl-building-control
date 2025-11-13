import axios from 'axios'
import { getBaseHost } from '@/services/api-service.ts'

const API_BASE = `${getBaseHost()}:8000/api/weather`

export const fetchWeatherFolders = async (): Promise<string[]> => {
  const response = await axios.get<{ epw_files: string[] }>(`${API_BASE}/all`)
  return response.data.epw_files ?? []
}
