import axios from 'axios'

import type { ExperimentDefinition } from '@/services/yaml-service.ts'
import { getBaseHost } from '@/services/api-service.ts'

const API_BASE = `${getBaseHost()}:8000/api/experiment`
const DEFAULT_DIRECTORY = './config/experiments'

export interface ExperimentConfigFileList {
  files: string[]
  fullPaths: string[]
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

export type ExperimentSuiteStatus =
  | 'New'
  | 'Running'
  | 'Finished'
  | 'Partially Successful'
  | 'Error'
  | 'Aborted'

export interface TensorBoardStatus {
  enabled: boolean
  running: boolean
  url?: string | null
  port?: number | null
  pid?: number | null
  owner?: string | null
  started_at?: string | null
  expires_at?: string | null
}

export interface TensorBoardStatusResponse extends TensorBoardStatus {
  suite_id: number
}

export interface StopTensorBoardResponse extends TensorBoardStatusResponse {
  stopped: boolean
}

export interface ExperimentSuiteApiResponse {
  id: number
  name: string
  status: ExperimentSuiteStatus
  pid?: number | null
  path?: string
  config_filename?: string
  archived: boolean
  tensorboard_enabled: boolean
  tensorboard: TensorBoardStatus
}

export interface ConfigDetailsSection {
  filename: string
  content: Record<string, unknown>
}

export interface SuiteContextFile {
  filename: string
  content: string
  original_path?: string | null
  relative_path: string
}

export interface SuiteContextExperiment {
  key: string
  id: number
  name: string
  experiment: SuiteContextFile
  environment?: SuiteContextFile | null
  controller?: SuiteContextFile | null
}

export interface SuiteContextResponse {
  suite_id: number
  hdf5_file: string
  experiments: SuiteContextExperiment[]
}

export interface ExperimentConfigDetailsResponse {
  experiment: ConfigDetailsSection
  environment?: ConfigDetailsSection | null
  controller?: ConfigDetailsSection | null
  experiments: ExperimentConfigDetailsExperiment[]
}

export interface ExperimentConfigDetailsExperiment {
  id: number
  name?: string | null
  environment?: ConfigDetailsSection | null
  controller?: ConfigDetailsSection | null
  environment_path?: string | null
  controller_path?: string | null
}

export interface ExperimentProgressResponse {
  id: number
  name?: string | null
  status?: string | null
  total_training_episodes?: number | undefined
  current_training_episode?: number | undefined
  total_evaluation_episodes?: number | undefined
  current_evaluation_episode?: number | undefined
}

export interface ExperimentRunStatusResponse {
  experiments: ExperimentProgressResponse[]
}

export interface ExperimentLogResponse {
  content: string
}

export interface RunExperimentSuitePayload {
  configName: string
  suiteName: string
}

export interface StopExperimentSuiteResponse {
  id: number
  status: ExperimentSuiteStatus
}

export interface ExperimentPathsResponse {
  files: string[]
  fullPaths: string[]
}

export const stripExperimentExtension = (value: string): string =>
  value.replace(/\.ya?ml$/i, '')

export const normalizeExperimentFilename = (value: string): string =>
  value.trim().toLowerCase()

export const EXPERIMENT_API_BASE = API_BASE

export const fetchExperimentConfigs =
  async (): Promise<ExperimentPathsResponse> => {
    const response = await axios.get<ExperimentConfigFileList>(
      `${API_BASE}/all`,
    )
    return {
      files: response.data.files,
      fullPaths: response.data.fullPaths,
    }
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

export const fetchExperimentSuites = async (): Promise<
  ExperimentSuiteApiResponse[]
> => {
  const response = await axios.get<ExperimentSuiteApiResponse[]>(
    `${API_BASE}/suites`,
  )
  return response.data
}

export const fetchSuiteContext = async (
  suiteId: number,
): Promise<SuiteContextResponse> => {
  const response = await axios.get<SuiteContextResponse>(
    `${API_BASE}/suites/${suiteId}/context`,
  )
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

export const archiveExperimentSuite = async (
  suiteId: number,
): Promise<ExperimentSuiteApiResponse> => {
  const response = await axios.post<ExperimentSuiteApiResponse>(
    `${API_BASE}/suites/${suiteId}/archive`,
  )
  return response.data
}

export const deleteExperimentSuite = async (suiteId: number): Promise<void> => {
  await axios.delete(`${API_BASE}/suites/${suiteId}`)
}

export const reproduceSuiteExperiment = async (
  suiteId: number,
  experimentKey: string,
  reproductionName?: string,
): Promise<ExperimentSuiteApiResponse> => {
  const response = await axios.post<ExperimentSuiteApiResponse>(
    `${API_BASE}/suites/${suiteId}/experiments/${encodeURIComponent(experimentKey)}/reproduce`,
    reproductionName !== undefined ? { name: reproductionName } : {},
  )
  return response.data
}

export const fetchExperimentConfigDetails = async (
  configName: string,
): Promise<ExperimentConfigDetailsResponse> => {
  const response = await axios.get<ExperimentConfigDetailsResponse>(
    `${API_BASE}/config-details/${configName}`,
  )
  return response.data
}

export const fetchExperimentSuiteStatus = async (
  suiteId: number,
): Promise<ExperimentRunStatusResponse> => {
  const response = await axios.get<ExperimentRunStatusResponse>(
    `${API_BASE}/suites/${suiteId}/status`,
  )
  return response.data
}

export const fetchExperimentSuiteLogs = async (
  suiteId: number,
): Promise<ExperimentLogResponse> => {
  const response = await axios.get<ExperimentLogResponse>(
    `${API_BASE}/suites/${suiteId}/logs`,
  )
  return response.data
}

export const createExperimentLogEventSource = (suiteId: number): EventSource =>
  new EventSource(`${API_BASE}/suites/${suiteId}/logs/stream`)

export const startTensorBoard = async (
  suiteId: number,
  owner?: string,
): Promise<TensorBoardStatusResponse> => {
  const payload = owner ? { owner } : undefined
  const response = await axios.post<TensorBoardStatusResponse>(
    `${API_BASE}/suites/${suiteId}/tensorboard/start`,
    payload,
  )
  return response.data
}

export const stopTensorBoard = async (
  suiteId: number,
  reason?: string,
): Promise<StopTensorBoardResponse> => {
  const payload = reason ? { reason } : undefined
  const response = await axios.post<StopTensorBoardResponse>(
    `${API_BASE}/suites/${suiteId}/tensorboard/stop`,
    payload,
  )
  return response.data
}
