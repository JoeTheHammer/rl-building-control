export const HYPERPARAMETER_SAMPLERS = [
  'tpe',
  'random',
  'grid',
  'cmaes',
  'nsgaii',
] as const

export type HyperparameterSampler =
  (typeof HYPERPARAMETER_SAMPLERS)[number]
