import type { KeyValue } from '../../shared/key-value-list.tsx'

export type ControllerType = 'reinforcement learning' | 'rule based' | 'custom'

export interface ControllerRule {
  condition: string
  action: string
}

export interface ControllerSettings {
  type: ControllerType
  trainingTimesteps?: number
  reportTraining: boolean
  denormalize: boolean
  tensorboardLogs: boolean
  hpTuning: boolean
  numEpisodes?: number
  numTrials?: number
  hyperparameters: KeyValue[]
  customVariables: KeyValue[]
  stateSpace: string[]
  rules: ControllerRule[]
  customModule: string
  customClassName: string
  initArguments: KeyValue[]
}
