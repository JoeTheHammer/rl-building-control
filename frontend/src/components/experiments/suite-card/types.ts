import type { MouseEventHandler } from 'react'

import type { ExperimentSuiteApiResponse } from '@/services/experiment-service.ts'

import type { LocalExperimentSuite } from '../types.ts'

export type Suite = LocalExperimentSuite | ExperimentSuiteApiResponse

export interface TensorboardControls {
  onOpen: MouseEventHandler<HTMLButtonElement>
  onStop: MouseEventHandler<HTMLButtonElement>
  disabled: boolean
  isLoading: boolean
  isRunning: boolean
  isStopping: boolean
}
