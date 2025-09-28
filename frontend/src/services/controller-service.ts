import axios from 'axios'

import type { ControllerSettings } from '@/components/configurator/controller/controller-types.ts'

const API_BASE = 'http://127.0.0.1:8000/api/controller'
const DEFAULT_DIRECTORY = './config/controllers'

export interface ControllerConfigFileList {
  files: string[]
}

export interface ControllerConfig {
  name: string
  content: Record<string, unknown>
}

export interface SaveControllerPayload {
  filename: string
  settings: ControllerSettings
  directory?: string
}

export const stripControllerExtension = (value: string): string =>
  value.replace(/\.ya?ml$/i, '')

export const normalizeControllerFilename = (value: string): string =>
  value.trim().toLowerCase()

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

export const saveControllerConfig = async ({
  filename,
  settings,
  directory = DEFAULT_DIRECTORY,
}: SaveControllerPayload): Promise<void> => {
  await axios.post(`${API_BASE}/save`, {
    filename,
    settings,
    directory,
  })
}
