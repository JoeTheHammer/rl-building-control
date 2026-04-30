import axios from 'axios'
import { getApiBase } from '@/services/api-service.ts'
import type {
  ExperimentSuiteApiResponse,
  SuiteContextResponse,
} from '@/services/experiment-service.ts'

const API_BASE = getApiBase('/api/analytics')

export type NumericSeries = number[]

export interface AnalyticsSeriesMap {
  [key: string]: NumericSeries
}

export interface AnalyticsEpisode {
  id: string
  label?: string | null
  reward: NumericSeries
  actions: AnalyticsSeriesMap
  states: AnalyticsSeriesMap
  measurements: AnalyticsSeriesMap
  metadata?: Record<string, unknown>
}

export interface AnalyticsEvaluation {
  action_names: string[]
  state_names: string[]
  measurement_names: string[]
  episodes: AnalyticsEpisode[]
  metadata?: Record<string, unknown>
}

export interface AnalyticsTraining {
  action_names: string[]
  state_names: string[]
  measurement_names: string[]
  reward: NumericSeries
  actions: AnalyticsSeriesMap
  states: AnalyticsSeriesMap
  measurements: AnalyticsSeriesMap
  metadata?: Record<string, unknown>
}

export interface AnalyticsExperiment {
  key: string
  name: string
  metadata?: Record<string, unknown>
  evaluation?: AnalyticsEvaluation | null
  training?: AnalyticsTraining | null
}

export interface AnalyticsDataResponse {
  suite_id: number
  suite_name: string
  file_name: string
  metadata?: Record<string, unknown>
  experiments: AnalyticsExperiment[]
}

export interface AnalyticsSuiteSummary {
  id: number
  name: string
  status: string
  path?: string | null
  config_filename?: string | null
  has_data: boolean
  file_name?: string | null
}

export interface DownloadedFile {
  blob: Blob
  fileName: string
}

const getFileNameFromDisposition = (header?: string | null): string | null => {
  if (!header) return null
  const match = /filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i.exec(header)
  if (!match) return null
  const value = match[1] || match[2]
  try {
    return decodeURIComponent(value)
  } catch {
    return value
  }
}

export const fetchAnalyticsSuites = async (): Promise<
  AnalyticsSuiteSummary[]
> => {
  const response = await axios.get<AnalyticsSuiteSummary[]>(
    `${API_BASE}/suites`,
  )
  return response.data
}

export const fetchAnalyticsSuiteData = async (
  suiteId: number,
): Promise<AnalyticsDataResponse> => {
  const response = await axios.get<AnalyticsDataResponse>(
    `${API_BASE}/suites/${suiteId}/data`,
  )
  return response.data
}

export const downloadAnalyticsSuiteFile = async (
  suiteId: number,
): Promise<DownloadedFile> => {
  const response = await axios.get(`${API_BASE}/suites/${suiteId}/file`, {
    responseType: 'blob',
  })
  const fileName =
    getFileNameFromDisposition(response.headers['content-disposition']) ||
    `suite-${suiteId}.h5`
  return {
    blob: response.data,
    fileName,
  }
}

export const uploadAnalyticsFile = async (
  file: File,
  onProgress?: (progress: number) => void,
): Promise<AnalyticsDataResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await axios.post<AnalyticsDataResponse>(
    `${API_BASE}/file`,
    formData,
    {
      params: { filename: file.name },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentComplete = Math.round(
            (progressEvent.loaded / progressEvent.total) * 100,
          )
          onProgress(percentComplete)
        }
      },
    },
  )
  return response.data
}

export const fetchUploadedAnalyticsContext = async (
  file: File,
): Promise<SuiteContextResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await axios.post<SuiteContextResponse>(
    `${API_BASE}/file/context`,
    formData,
    {
      params: { filename: file.name },
    },
  )
  return response.data
}

export const reproduceUploadedAnalyticsExperiment = async (
  file: File,
  experimentKey: string,
  reproductionName?: string,
): Promise<ExperimentSuiteApiResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await axios.post<ExperimentSuiteApiResponse>(
    `${API_BASE}/file/experiments/${encodeURIComponent(experimentKey)}/reproduce`,
    formData,
    {
      params: {
        filename: file.name,
        ...(reproductionName !== undefined ? { name: reproductionName } : {}),
      },
    },
  )
  return response.data
}
