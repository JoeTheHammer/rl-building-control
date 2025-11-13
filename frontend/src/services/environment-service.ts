import axios from 'axios'

import type { EnvironmentGeneralSettings } from '@/components/configurator/environment/env-general-tab.tsx'
import type { EnvironmentStateSpaceSettings } from '@/components/configurator/environment/env-state-space-tab.tsx'
import type { EnvActionSpaceSettings } from '@/components/configurator/environment/env-action-space-tab.tsx'
import type { EnvironmentRewardSettings } from '@/components/configurator/environment/env-reward-tab.tsx'
import { getBaseHost } from '@/services/api-service.ts'

const API_BASE = `${getBaseHost()}:8000/api/environment`
const DEFAULT_DIRECTORY = './config/environments'

export interface EnvironmentConfigFileList {
  files: string[]
}

export interface EnvironmentConfig {
  name: string
  content: Record<string, unknown> // instead of `any`
}

export interface SaveEnvironmentPayload {
  filename: string
  config: {
    generalSettings: EnvironmentGeneralSettings
    stateSpaceSettings: EnvironmentStateSpaceSettings
    actionSpaceSettings: EnvActionSpaceSettings
    rewardSettings: EnvironmentRewardSettings
  }
  directory?: string
}

export const stripEnvironmentExtension = (value: string): string =>
  value.replace(/\.ya?ml$/i, '')

export const normalizeEnvironmentFilename = (value: string): string =>
  value.trim().toLowerCase()

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

export const saveEnvironmentConfig = async ({
  filename,
  config,
  directory = DEFAULT_DIRECTORY,
}: SaveEnvironmentPayload): Promise<void> => {
  await axios.post(`${API_BASE}/save`, {
    filename,
    config,
    directory,
  })
}
