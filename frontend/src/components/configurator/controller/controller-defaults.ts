import type { KeyValue } from '../../shared/key-value-list.tsx'

export const CONTROLLER_HYPERPARAMETER_SUGGESTIONS: KeyValue[] = []

export const getDefaultControllerHyperparameters = (): KeyValue[] =>
  CONTROLLER_HYPERPARAMETER_SUGGESTIONS.map(({ key, value }) => ({
    key,
    value,
  }))
