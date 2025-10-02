import axios from 'axios'

const API_BASE = 'http://127.0.0.1:8000/api/weather'

export const fetchWeatherFolders = async (): Promise<string[]> => {
  const response = await axios.get<{ epw_files: string[] }>(`${API_BASE}/all`)
  return response.data.epw_files ?? []
}
