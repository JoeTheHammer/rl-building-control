import type { KeyValue } from '../../shared/key-value-list.tsx'

export const CONTROLLER_HYPERPARAMETER_SUGGESTIONS: KeyValue[] = [
  { key: 'learning_rate', value: '0.0001' },
  { key: 'gamma', value: '0.99' },
  { key: 'tensorboard_log', value: 'logs/' },
]

export const getDefaultControllerHyperparameters = (): KeyValue[] =>
  CONTROLLER_HYPERPARAMETER_SUGGESTIONS.map(({ key, value }) => ({
    key,
    value,
  }))
