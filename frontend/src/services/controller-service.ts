import axios from 'axios'

const API_BASE = 'http://127.0.0.1:8000/api/controller'

export interface ControllerConfigFileList {
  files: string[]
}

export interface ControllerConfig {
  name: string
  content: Record<string, unknown>
}

export const fetchControllerConfigs = async (): Promise<string[]> => {
  const response = await axios.get<ControllerConfigFileList>(`${API_BASE}/all`)
  return response.data.files
}

export const fetchControllerConfig = async (
  name: string,
): Promise<ControllerConfig> => {
  const response = await axios.get<ControllerConfig>(`${API_BASE}/${name}`)
  return response.data
}
