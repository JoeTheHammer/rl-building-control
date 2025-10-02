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

export type ExperimentSuiteStatus = 'New' | 'Running' | 'Finished' | 'Aborted'

export interface ExperimentSuiteApiResponse {
  id: number
  name: string
  status: ExperimentSuiteStatus
  pid?: number | null
}

export interface RunExperimentSuitePayload {
  configName: string
  suiteName: string
}

export interface StopExperimentSuiteResponse {
  id: number
  status: ExperimentSuiteStatus
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

export const fetchExperimentSuites = async (): Promise<ExperimentSuiteApiResponse[]> => {
  const response = await axios.get<ExperimentSuiteApiResponse[]>(`${API_BASE}/suites`)
  return response.data
}

export const runExperimentSuite = async ({
  configName,
  suiteName,
}: RunExperimentSuitePayload): Promise<ExperimentSuiteApiResponse> => {
  const response = await axios.post<ExperimentSuiteApiResponse>(
    `${API_BASE}/suites/run`,
    {
      config_name: configName,
      suite_name: suiteName,
    },
  )
  return response.data
}

export const stopExperimentSuite = async (
  suiteId: number,
): Promise<StopExperimentSuiteResponse> => {
  const response = await axios.post<StopExperimentSuiteResponse>(
    `${API_BASE}/suites/${suiteId}/stop`,
  )
  return response.data
}
