import type { KeyValue } from '../../shared/key-value-list.tsx'
import type { HyperparameterSampler } from '@/constants/hyperparameter-samplers.ts'

export type ControllerType = 'reinforcement learning' | 'rule based' | 'custom'

export interface ControllerRule {
  condition: string
  action: string
}

export interface EnvironmentWrapperSettings {
  normalizeState: boolean
  normalizeReward: boolean
  normalizeAction: boolean
  continuousAction: boolean
  discreteAction: boolean
}

export const createDefaultEnvironmentWrapperSettings = (): EnvironmentWrapperSettings => ({
  normalizeState: true,
  normalizeReward: true,
  normalizeAction: true,
  continuousAction: true,
  discreteAction: false,
})

export interface ControllerSettings {
  type: ControllerType
  trainingTimesteps?: number
  reportTraining: boolean
  denormalize: boolean
  tensorboardLogs: boolean
  hpTuning: boolean
  hpSampler: HyperparameterSampler
  hpTrainingTimesteps?: number
  numEpisodes?: number
  numTrials?: number
  hyperparameters: KeyValue[]
  environmentWrapper: EnvironmentWrapperSettings
  customVariables: KeyValue[]
  stateSpace: string[]
  rules: ControllerRule[]
  customModule: string
  customClassName: string
  initArguments: KeyValue[]
}
