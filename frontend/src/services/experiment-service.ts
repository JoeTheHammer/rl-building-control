import axios from 'axios'

import type { ExperimentDefinition } from '@/services/yaml-service.ts'

const API_BASE = 'http://127.0.0.1:8000/api/experiment'
const DEFAULT_DIRECTORY = './config/experiments'

export interface ExperimentConfigFileList {
  files: string[]
}

export interface ExperimentConfig {
  name: string
  content: Record<string, unknown>
}

export interface SaveExperimentPayload {
  filename: string
  experiments: ExperimentDefinition[]
  directory?: string
}

export const stripExperimentExtension = (value: string): string =>
  value.replace(/\.ya?ml$/i, '')

export const normalizeExperimentFilename = (value: string): string =>
  value.trim().toLowerCase()

export const fetchExperimentConfigs = async (): Promise<string[]> => {
  const response = await axios.get<ExperimentConfigFileList>(`${API_BASE}/all`)
  return response.data.files
}

export const fetchExperimentConfig = async (
  name: string,
): Promise<ExperimentConfig> => {
  const response = await axios.get<ExperimentConfig>(`${API_BASE}/${name}`)
  return response.data
}

export const saveExperimentConfig = async ({
  filename,
  experiments,
  directory = DEFAULT_DIRECTORY,
}: SaveExperimentPayload): Promise<void> => {
  await axios.post(`${API_BASE}/save`, {
    filename,
    experiments,
    directory,
  })
}
