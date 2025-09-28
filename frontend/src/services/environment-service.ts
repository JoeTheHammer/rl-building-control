import axios from 'axios'

const API_BASE = 'http://127.0.0.1:8000/api/environment'

export interface EnvironmentConfigFileList {
  files: string[]
}

export interface EnvironmentConfig {
  name: string
  content: Record<string, unknown> // instead of `any`
}

export const fetchEnvironmentConfigs = async (): Promise<string[]> => {
  const response = await axios.get<EnvironmentConfigFileList>(`${API_BASE}/all`)
  return response.data.files
}

export const fetchEnvironmentConfig = async (
  name: string,
): Promise<EnvironmentConfig> => {
  const response = await axios.get<EnvironmentConfig>(`${API_BASE}/${name}`)
  return response.data
}
