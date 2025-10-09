import axios from 'axios'

const API_BASE = 'http://127.0.0.1:8000/api/analytics'

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

export const fetchAnalyticsSuites = async (): Promise<AnalyticsSuiteSummary[]> => {
  const response = await axios.get<AnalyticsSuiteSummary[]>(`${API_BASE}/suites`)
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
