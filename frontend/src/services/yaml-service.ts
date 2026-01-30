import yaml from 'js-yaml'
import type { EnvironmentRewardSettings } from '@/components/configurator/environment/env-reward-tab.tsx'
import type { EnvActionSpaceSettings } from '@/components/configurator/environment/env-action-space-tab.tsx'
import type { EnvironmentStateSpaceSettings } from '@/components/configurator/environment/env-state-space-tab.tsx'
import type { EnvironmentGeneralSettings } from '@/components/configurator/environment/env-general-tab.tsx'
import type {
  ControllerRule,
  ControllerSettings,
  ControllerType,
} from '@/components/configurator/controller/controller-types.ts'
import { createDefaultEnvironmentWrapperSettings } from '@/components/configurator/controller/controller-types.ts'
import type { KeyValue } from '@/components/shared/key-value-list.tsx'
import { getDefaultControllerHyperparameters } from '@/components/configurator/controller/controller-defaults.ts'
import {
  HYPERPARAMETER_SAMPLERS,
  type HyperparameterSampler,
} from '@/constants/hyperparameter-samplers.ts'

export interface EnvironmentConfig {
  generalSettings: EnvironmentGeneralSettings
  stateSpaceSettings: EnvironmentStateSpaceSettings
  actionSpaceSettings: EnvActionSpaceSettings
  rewardSettings: EnvironmentRewardSettings
}

const CONTROLLER_TYPES: ControllerType[] = [
  'reinforcement learning',
  'rule based',
  'custom',
]

const isHyperparameterSampler = (
  value: string,
): value is HyperparameterSampler =>
  (HYPERPARAMETER_SAMPLERS as readonly string[]).includes(value)

const normalizeSampler = (value: unknown): HyperparameterSampler => {
  if (typeof value !== 'string') {
    return 'tpe'
  }

  const normalized = value.trim().toLowerCase()

  return isHyperparameterSampler(normalized) ? normalized : 'tpe'
}

const normalizeFile = (
  file: File | string | null | undefined,
): string | null => {
  if (!file) return null
  if (typeof file === 'string') return file
  if (file instanceof File) return file.name
  return null
}

export const buildEnvironmentYaml = (
  general: EnvironmentGeneralSettings,
  state: EnvironmentStateSpaceSettings,
  action: EnvActionSpaceSettings,
  reward: EnvironmentRewardSettings,
): string => {
  const variables: Record<
    string,
    { name: string; zone: string; exclude_from_state?: boolean }
  > = {}
  const meters: Record<
    string,
    string | { name: string; exclude_from_state?: boolean }
  > = {}

  state.variables.forEach((v) => {
    if (v.variableType === 'meter') {
      if (v.excludeFromState) {
        meters[v.name] = {
          name: v.meterName,
          exclude_from_state: true,
        }
      } else {
        meters[v.name] = v.meterName
      }
    } else {
      variables[v.name] = {
        name: v.energyPlusName,
        zone: v.zone,
        ...(v.excludeFromState ? { exclude_from_state: true } : {}),
      }
    }
  })
  const parseDate = (date: string) => {
    if (!date) return []
    const d = new Date(date)
    if (isNaN(d.getTime())) return []
    return [d.getDate(), d.getMonth() + 1, d.getFullYear()]
  }
  const start = parseDate(general.startDate)
  const end = parseDate(general.endDate)
  // only include if both are valid
  const period =
    start.length === 3 && end.length === 3 ? [...start, ...end] : []

  const doc = {
    building_model: normalizeFile(general.buildingModelFile),
    weather_data: normalizeFile(general.weatherDataFile),
    state_space: {
      ...(Object.keys(variables).length > 0 ? { variables } : {}),
      ...(Object.keys(meters).length > 0 ? { meters } : {}),
      time_info: {
        day_of_month: { cyclic: state.dayOfMonth.cyclic },
        month: { cyclic: state.month.cyclic },
        day_of_week: { cyclic: state.dayOfWeek.cyclic },
        hour: { cyclic: state.hour.cyclic },
      },
    },
    action_space: {
      actuators: Object.fromEntries(
        action.actuators.map((a) => {
          if (a.type === 'continuous') {
            return [
              a.actuatorName,
              {
                type: 'continuous',
                range: [a.min, a.max],
                component: a.component,
                control_type: a.controlType,
                actuator_key: a.actuatorKey,
              },
            ]
          } else if (a.type === 'discrete' && a.mode === 'range') {
            return [
              a.actuatorName,
              {
                type: 'discrete',
                range: [a.min, a.max],
                step_size: a.stepSize,
                component: a.component,
                control_type: a.controlType,
                actuator_key: a.actuatorKey,
              },
            ]
          } else if (a.type === 'discrete' && a.mode === 'values') {
            return [
              a.actuatorName,
              {
                type: 'discrete',
                values: a.valueList,
                component: a.component,
                control_type: a.controlType,
                actuator_key: a.actuatorKey,
              },
            ]
          }
          return [a.actuatorName, {}]
        }),
      ),
    },
    reward_function: {
      type: reward.type,
      variables: reward.variables,
      expression: reward.expression,
      params: Object.fromEntries(
        reward.parameters.map((p) => [p.key, p.value]),
      ),
      // UPDATED: Filter out entries with empty keys to prevent overwriting
      init_args: reward.init_args
        ? Object.fromEntries(
            reward.init_args
              .filter((p) => p.key && p.key.trim() !== '') // Only keep valid keys
              .map((p) => [p.key, p.value]),
          )
        : undefined,
      module: reward.module,
      class_name: reward.class_name,
    },
    episode: {
      timesteps_per_hour: general.timestepsPerHour,
      period,
    },
  }

  const weatherVariabilityEntries = general.weatherVariabilityVariables.filter(
    (entry) => entry.key.trim() !== '',
  )
  if (general.weatherVariabilityEnabled && weatherVariabilityEntries.length > 0) {
    Object.assign(doc, {
      weather_variability: Object.fromEntries(
        weatherVariabilityEntries.map((entry) => [
          entry.key,
          [entry.sigma, entry.mu, entry.tau],
        ]),
      ),
    })
  }

  return yaml.dump(doc, { noRefs: true })
}

interface ParsedDoc {
  building_model?: string
  weather_data?: string
  weather_variability?: Record<string, [number, number, number]>
  state_space?: {
    variables?: Record<
      string,
      { name?: string; type?: string; zone: string; exclude_from_state?: boolean }
    >
    meters?: Record<
      string,
      string | { name: string; exclude_from_state?: boolean }
    >
    time_info?: {
      day_of_month?: { cyclic: boolean }
      month?: { cyclic: boolean }
      day_of_week?: { cyclic: boolean }
      hour?: { cyclic: boolean }
    }
  }
  action_space?: {
    actuators?: Record<
      string,
      | {
          type: 'continuous'
          range: [number, number]
          component: string
          control_type: string
          actuator_key: string
        }
      | {
          type: 'discrete'
          values: number[]
          component: string
          control_type: string
          actuator_key: string
        }
      | {
          type: 'discrete'
          range: [number, number]
          step_size: number
          component: string
          control_type: string
          actuator_key: string
        }
    >
  }
  reward_function?: {
    type: string
    variables?: string[]
    expression?: string
    params?: Record<string, number | string>
    module?: string
    class_name?: string
    init_args?: Record<string, unknown>
  }
  episode?: {
    timesteps_per_hour?: number
    period?: number[]
  }
}

export const parseEnvironmentYaml = (yamlStr: string): EnvironmentConfig => {
  const doc = yaml.load(yamlStr) as ParsedDoc

  const weatherVariabilityEntries = Object.entries(
    doc.weather_variability ?? {},
  ).map(([key, values]) => ({
    key,
    sigma: values?.[0] ?? 0,
    mu: values?.[1] ?? 0,
    tau: values?.[2] ?? 0,
  }))

  const generalSettings: EnvironmentGeneralSettings = {
    buildingModelFile: doc.building_model ?? null,
    weatherDataFile: doc.weather_data ?? null,
    startDate: doc.episode?.period
      ? `${doc.episode.period[2]}-${doc.episode.period[1]}-${doc.episode.period[0]}`
      : '',
    endDate: doc.episode?.period
      ? `${doc.episode.period[5]}-${doc.episode.period[4]}-${doc.episode.period[3]}`
      : '',
    timestepsPerHour: doc.episode?.timesteps_per_hour ?? undefined,
    weatherVariabilityEnabled: weatherVariabilityEntries.length > 0,
    weatherVariabilityVariables: weatherVariabilityEntries,
  }

  const variables =
    Object.entries(doc.state_space?.variables ?? {}).map(([name, v]) => ({
      name,
      variableType: 'variable' as const,
      energyPlusName: v.name ?? v.type ?? '',
      zone: v.zone,
      excludeFromState: !!v.exclude_from_state,
    })) ?? []

  const meters =
    Object.entries(doc.state_space?.meters ?? {}).map(([name, meterValue]) => {
      if (typeof meterValue === 'string') {
        return {
          name,
          variableType: 'meter' as const,
          meterName: meterValue,
          excludeFromState: false,
        }
      }

      return {
        name,
        variableType: 'meter' as const,
        meterName: meterValue.name,
        excludeFromState: !!meterValue.exclude_from_state,
      }
    }) ?? []

  const stateSpaceSettings: EnvironmentStateSpaceSettings = {
    addTimeInfo: !!doc.state_space?.time_info,
    dayOfMonth: {
      included: !!doc.state_space?.time_info?.day_of_month,
      cyclic: !!doc.state_space?.time_info?.day_of_month?.cyclic,
    },
    month: {
      included: !!doc.state_space?.time_info?.month,
      cyclic: !!doc.state_space?.time_info?.month?.cyclic,
    },
    dayOfWeek: {
      included: !!doc.state_space?.time_info?.day_of_week,
      cyclic: !!doc.state_space?.time_info?.day_of_week?.cyclic,
    },
    hour: {
      included: !!doc.state_space?.time_info?.hour,
      cyclic: !!doc.state_space?.time_info?.hour?.cyclic,
    },
    minute: { included: false, cyclic: false }, // not stored in YAML
    variables: [...variables, ...meters],
  }

  const actuators =
    Object.entries(doc.action_space?.actuators ?? {}).map(([name, a]) => {
      if (a.type === 'continuous') {
        return {
          actuatorName: name,
          component: a.component,
          controlType: a.control_type,
          actuatorKey: a.actuator_key,
          type: 'continuous' as const,
          mode: undefined,
          valueList: [],
          min: a.range?.[0],
          max: a.range?.[1],
          stepSize: undefined,
        }
      } else if (a.type === 'discrete' && 'values' in a) {
        return {
          actuatorName: name,
          component: a.component,
          controlType: a.control_type,
          actuatorKey: a.actuator_key,
          type: 'discrete' as const,
          mode: 'values' as const,
          valueList: a.values,
          min: undefined,
          max: undefined,
          stepSize: undefined,
        }
      } else if (a.type === 'discrete' && 'range' in a) {
        return {
          actuatorName: name,
          component: a.component,
          controlType: a.control_type,
          actuatorKey: a.actuator_key,
          type: 'discrete' as const,
          mode: 'range' as const,
          valueList: [],
          min: a.range?.[0],
          max: a.range?.[1],
          stepSize: a.step_size,
        }
      }
      return {
        actuatorName: name,
        component: '',
        controlType: '',
        actuatorKey: '',
        type: 'continuous' as const,
        mode: undefined,
        valueList: [],
      }
    }) ?? []

  const actionSpaceSettings: EnvActionSpaceSettings = { actuators }

  const rewardSettings: EnvironmentRewardSettings = {
    type:
      (doc.reward_function?.type as EnvironmentRewardSettings['type']) ??
      'expression',

    variables: Array.isArray(doc.reward_function?.variables)
      ? (doc.reward_function?.variables as string[])
      : [],

    parameters: Object.entries(doc.reward_function?.params ?? {})
      .filter(([, value]) => typeof value === 'number')
      .map(([key, value]) => ({ key, value: value as number })),

    expression: doc.reward_function?.expression ?? '',
    module: doc.reward_function?.module ?? '',
    class_name: doc.reward_function?.class_name ?? '',

    init_args:
      doc.reward_function?.init_args &&
      typeof doc.reward_function.init_args === 'object' &&
      !Array.isArray(doc.reward_function.init_args)
        ? Object.entries(doc.reward_function.init_args).map(([key, value]) => ({
            key,
            // Ensure values are converted to strings for the Input fields
            value: value === null || value === undefined ? '' : String(value),
          }))
        : [],
  }

  return {
    generalSettings,
    stateSpaceSettings,
    actionSpaceSettings,
    rewardSettings,
  }
}

const toYamlPrimitive = (value: string): string | number | boolean => {
  const trimmed = value.trim()
  if (trimmed === '') return ''

  const lower = trimmed.toLowerCase()
  if (lower === 'true') return true
  if (lower === 'false') return false

  const numericPattern = /^-?\d+(?:_\d+)*(?:\.\d+)?$/
  if (numericPattern.test(trimmed)) {
    const normalized = trimmed.replaceAll('_', '')
    const numeric = Number(normalized)
    if (!Number.isNaN(numeric)) {
      return numeric
    }
  }

  return trimmed
}

const keyValueArrayToRecord = (values: KeyValue[]): Record<string, unknown> => {
  return values
    .map(({ key, value }) => ({ key: key.trim(), value }))
    .filter(({ key }) => key.length > 0)
    .reduce<Record<string, unknown>>((acc, current) => {
      acc[current.key] = toYamlPrimitive(current.value)
      return acc
    }, {})
}

interface ControllerYamlDoc {
  type?: unknown
  training?: {
    timesteps?: unknown
    report_training?: unknown
    report_denormalized_state?: unknown
    tensorboard_logs?: unknown
  }
  hyperparameter_tuning?: {
    num_trials?: unknown
    num_episodes?: unknown
    enabled?: boolean
    sampler?: unknown
    training_timesteps?: unknown
  } | null
  hyperparameters?: Record<string, unknown>
  environment_wrapper?: {
    normalize_state?: unknown
    normalize_reward?: unknown
    normalize_action?: unknown
    continuous_action?: unknown
    discrete_action?: unknown
  }
  state_space?: unknown
  custom_variables?: Record<string, unknown>
  rules?: { condition?: unknown; action?: unknown }[]
  module?: unknown
  class_name?: unknown
  args?: Record<string, unknown>
}

const recordToKeyValueArray = (
  record?: Record<string, unknown>,
): KeyValue[] => {
  if (!record) {
    return []
  }

  return Object.entries(record).map(([key, value]) => ({
    key,
    value:
      value === null || value === undefined
        ? ''
        : typeof value === 'object'
          ? JSON.stringify(value)
          : String(value),
  }))
}

const sanitizeRules = (rules: ControllerRule[]): ControllerRule[] =>
  rules
    .map((rule) => ({
      condition: rule.condition.trim(),
      action: rule.action.trim(),
    }))
    .filter((rule) => rule.condition.length > 0 || rule.action.length > 0)

const createDefaultRule = (): ControllerRule => ({ condition: '', action: '' })

export const buildControllerYaml = (settings: ControllerSettings): string => {
  if (settings.type === 'custom') {
    const doc: Record<string, unknown> = {}

    const className = settings.customClassName.trim()
    if (className.length > 0) {
      doc.class_name = className
    }

    const modulePath = settings.customModule.trim()
    if (modulePath.length > 0) {
      doc.module = modulePath
    }

    const argsRecord = keyValueArrayToRecord(settings.initArguments)
    if (Object.keys(argsRecord).length > 0) {
      doc.args = argsRecord
    }

    if (Object.keys(doc).length === 0) {
      doc.type = settings.type
    }

    return yaml.dump(doc, { noRefs: true })
  }

  if (settings.type === 'rule based') {
    const stateSpaceValues = settings.stateSpace
      .map((value) => value.trim())
      .filter(Boolean)
    const customVariablesRecord = keyValueArrayToRecord(
      settings.customVariables,
    )
    const rules = sanitizeRules(settings.rules).map((rule) => ({
      condition: rule.condition,
      action: rule.action,
    }))

    const doc: Record<string, unknown> = {}

    if (stateSpaceValues.length > 0) {
      doc.state_space = stateSpaceValues
    }

    if (Object.keys(customVariablesRecord).length > 0) {
      doc.custom_variables = customVariablesRecord
    }

    if (rules.length > 0) {
      doc.rules = rules
    }

    return yaml.dump(doc, { noRefs: true })
  }

  const hyperparametersRecord = keyValueArrayToRecord(settings.hyperparameters)

  const training: Record<string, unknown> = {
    report_training: settings.reportTraining,
    report_denormalized_state: settings.denormalize,
    tensorboard_logs: settings.tensorboardLogs,
  }

  if (typeof settings.trainingTimesteps === 'number') {
    training.timesteps = settings.trainingTimesteps
  }

  const doc: Record<string, unknown> = {
    training,
  }

  doc.environment_wrapper = {
    normalize_state: settings.environmentWrapper.normalizeState,
    normalize_reward: settings.environmentWrapper.normalizeReward,
    normalize_action: settings.environmentWrapper.normalizeAction,
    continuous_action: settings.environmentWrapper.continuousAction,
    discrete_action: settings.environmentWrapper.discreteAction,
  }

  if (settings.hpTuning) {
    const hpTuning: Record<string, unknown> = { enabled: true }
    if (typeof settings.numTrials === 'number') {
      hpTuning.num_trials = settings.numTrials
    }
    if (typeof settings.numEpisodes === 'number') {
      hpTuning.num_episodes = settings.numEpisodes
    }
    if (settings.hpSampler) {
      hpTuning.sampler = settings.hpSampler
    }
    if (typeof settings.hpTrainingTimesteps === 'number') {
      hpTuning.training_timesteps = settings.hpTrainingTimesteps
    }
    doc.hyperparameter_tuning = hpTuning
  }

  if (Object.keys(hyperparametersRecord).length > 0) {
    doc.hyperparameters = hyperparametersRecord
  }

  return yaml.dump(doc, { noRefs: true })
}

export const parseControllerYaml = (yamlStr: string): ControllerSettings => {
  const doc = (yaml.load(yamlStr) as ControllerYamlDoc) ?? {}

  const explicitType =
    typeof doc.type === 'string' &&
    CONTROLLER_TYPES.includes(doc.type as ControllerType)
      ? (doc.type as ControllerType)
      : undefined

  const hasRuleBasedShape =
    Array.isArray(doc.rules) ||
    Array.isArray(doc.state_space) ||
    !!doc.custom_variables

  const hasCustomShape =
    typeof doc.module === 'string' ||
    typeof doc.class_name === 'string' ||
    (doc.args && typeof doc.args === 'object')

  const resolvedType: ControllerType =
    explicitType ??
    (hasRuleBasedShape
      ? 'rule based'
      : hasCustomShape
        ? 'custom'
        : 'reinforcement learning')

  const resolveControllerBoolean = (
    value: unknown,
    defaultValue: boolean,
  ): boolean => {
    if (typeof value === 'boolean') {
      return value
    }

    if (typeof value === 'string') {
      const normalized = value.trim().toLowerCase()
      if (normalized === 'true') return true
      if (normalized === 'false') return false
    }

    return defaultValue
  }

  if (resolvedType === 'rule based') {
    const rules = Array.isArray(doc.rules)
      ? doc.rules.map((rule) => ({
          condition: typeof rule?.condition === 'string' ? rule.condition : '',
          action: typeof rule?.action === 'string' ? rule.action : '',
        }))
      : []

    const stateSpaceArray = Array.isArray(doc.state_space)
      ? (doc.state_space.filter(
          (value) => typeof value === 'string',
        ) as string[])
      : []

    return {
      type: 'rule based',
      trainingTimesteps: undefined,
      reportTraining: false,
      denormalize: false,
      tensorboardLogs: false,
      hpTuning: false,
      hpSampler: 'tpe',
      numEpisodes: undefined,
      numTrials: undefined,
      hyperparameters: getDefaultControllerHyperparameters(),
      environmentWrapper: createDefaultEnvironmentWrapperSettings(),
      customVariables: recordToKeyValueArray(doc.custom_variables),
      stateSpace: stateSpaceArray,
      rules: rules.length > 0 ? rules : [createDefaultRule()],
      customModule: '',
      customClassName: '',
      initArguments: [],
    }
  }

  if (resolvedType === 'custom') {
    const argsList = recordToKeyValueArray(doc.args)

    return {
      type: 'custom',
      trainingTimesteps: undefined,
      reportTraining: false,
      denormalize: false,
      tensorboardLogs: false,
      hpTuning: false,
      hpSampler: 'tpe',
      numEpisodes: undefined,
      numTrials: undefined,
      hyperparameters: [],
      environmentWrapper: createDefaultEnvironmentWrapperSettings(),
      customVariables: [],
      stateSpace: [],
      rules: [createDefaultRule()],
      customModule: typeof doc.module === 'string' ? doc.module : '',
      customClassName: typeof doc.class_name === 'string' ? doc.class_name : '',
      initArguments: argsList,
    }
  }

  const training = doc.training ?? {}
  const hyperparameterTuning = doc.hyperparameter_tuning ?? null
  const environmentWrapperDoc = doc.environment_wrapper ?? {}

  const hyperparametersEntries = Object.entries(doc.hyperparameters ?? {})
  const hyperparameters = hyperparametersEntries.length
    ? hyperparametersEntries.map(([key, value]) => ({
        key,
        value:
          value === null || value === undefined
            ? ''
            : typeof value === 'object'
              ? JSON.stringify(value)
              : String(value),
      }))
    : getDefaultControllerHyperparameters()

  const environmentWrapper = createDefaultEnvironmentWrapperSettings()

  environmentWrapper.normalizeState = resolveControllerBoolean(
    environmentWrapperDoc.normalize_state,
    environmentWrapper.normalizeState,
  )
  environmentWrapper.normalizeReward = resolveControllerBoolean(
    environmentWrapperDoc.normalize_reward,
    environmentWrapper.normalizeReward,
  )
  environmentWrapper.normalizeAction = resolveControllerBoolean(
    environmentWrapperDoc.normalize_action,
    environmentWrapper.normalizeAction,
  )
  environmentWrapper.continuousAction = resolveControllerBoolean(
    environmentWrapperDoc.continuous_action,
    environmentWrapper.continuousAction,
  )
  environmentWrapper.discreteAction = resolveControllerBoolean(
    environmentWrapperDoc.discrete_action,
    environmentWrapper.discreteAction,
  )

  if (
    environmentWrapper.continuousAction === environmentWrapper.discreteAction
  ) {
    if ('discrete_action' in environmentWrapperDoc) {
      const discretePreferred = resolveControllerBoolean(
        environmentWrapperDoc.discrete_action,
        false,
      )
      environmentWrapper.discreteAction = discretePreferred
      environmentWrapper.continuousAction = !discretePreferred
    } else if ('continuous_action' in environmentWrapperDoc) {
      const continuousPreferred = resolveControllerBoolean(
        environmentWrapperDoc.continuous_action,
        true,
      )
      environmentWrapper.continuousAction = continuousPreferred
      environmentWrapper.discreteAction = !continuousPreferred
    } else {
      environmentWrapper.continuousAction = true
      environmentWrapper.discreteAction = false
    }
  }

  const sampler = normalizeSampler(hyperparameterTuning?.sampler)

  return {
    type: resolvedType,
    trainingTimesteps:
      typeof training.timesteps === 'number' ? training.timesteps : undefined,
    reportTraining: training.report_training === true,
    denormalize: training.report_denormalized_state === true,
    tensorboardLogs: training.tensorboard_logs === true,
    hpTuning:
      (hyperparameterTuning !== null &&
        hyperparameterTuning !== undefined &&
        hyperparameterTuning.enabled) ??
      false,
    hpSampler: sampler,
    hpTrainingTimesteps:
      typeof hyperparameterTuning?.training_timesteps === 'number'
        ? hyperparameterTuning.training_timesteps
        : undefined,
    numTrials:
      typeof hyperparameterTuning?.num_trials === 'number'
        ? hyperparameterTuning.num_trials
        : undefined,
    numEpisodes:
      typeof hyperparameterTuning?.num_episodes === 'number'
        ? hyperparameterTuning.num_episodes
        : undefined,
    hyperparameters,
    environmentWrapper,
    customVariables: [],
    stateSpace: [],
    rules: [createDefaultRule()],
    customModule: '',
    customClassName: '',
    initArguments: [],
  }
}

export interface ExperimentReportingOptions {
  denormalizeState: boolean
}

export interface ExperimentFormState {
  name: string
  engine: string
  environmentConfig: string
  controller: string
  controllerConfig: string
  episodes: number | undefined
  reporting: ExperimentReportingOptions
}

export interface ExperimentDefinition {
  name: string
  engine: string
  environmentConfig: string
  controller: string
  controllerConfig: string
  episodes: number
  reporting: ExperimentReportingOptions
}

interface ExperimentYamlEntry {
  name?: unknown
  engine?: unknown
  environment_config?: unknown
  controller?: unknown
  controller_config?: unknown
  episodes?: unknown
  reporting?: {
    denormalize_state?: unknown
  }
}

interface ExperimentsYamlDoc {
  experiments?: ExperimentYamlEntry[]
}

const resolveExperimentString = (value: unknown): string =>
  typeof value === 'string' ? value : ''

const resolveExperimentNumber = (value: unknown): number | undefined => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }

  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value)
    return Number.isNaN(parsed) ? undefined : parsed
  }

  return undefined
}

const resolveExperimentBoolean = (value: unknown): boolean => value === true

const resolveReporting = (
  experiment: ExperimentFormState,
): ExperimentReportingOptions => ({
  denormalizeState: experiment.reporting.denormalizeState,
})

export const buildExperimentYaml = (
  experiments: ExperimentFormState[],
): string => {
  const doc = {
    experiments: experiments.map((experiment) => ({
      name: experiment.name,
      engine: experiment.engine,
      environment_config: experiment.environmentConfig,
      controller: experiment.controller,
      controller_config: experiment.controllerConfig,
      episodes:
        typeof experiment.episodes === 'number' ? experiment.episodes : 0,
      reporting: {
        denormalize_state: experiment.reporting.denormalizeState,
      },
    })),
  }

  return yaml.dump(doc, { noRefs: true })
}

export const parseExperimentYaml = (yamlStr: string): ExperimentFormState[] => {
  const parsed = yaml.load(yamlStr) as
    | ExperimentsYamlDoc
    | ExperimentYamlEntry[]
    | null

  const experimentsArray: ExperimentYamlEntry[] = Array.isArray(parsed)
    ? parsed
    : (parsed?.experiments ?? [])

  return experimentsArray.map((experiment) => {
    const reporting = experiment.reporting ?? {}
    const reportingOptions: ExperimentReportingOptions = {
      denormalizeState: resolveExperimentBoolean(reporting.denormalize_state),
    }

    return {
      name: resolveExperimentString(experiment.name),
      engine: resolveExperimentString(experiment.engine),
      environmentConfig: resolveExperimentString(experiment.environment_config),
      controller: resolveExperimentString(experiment.controller),
      controllerConfig: resolveExperimentString(experiment.controller_config),
      episodes: resolveExperimentNumber(experiment.episodes),
      reporting: reportingOptions,
    }
  })
}

export const toExperimentDefinitions = (
  experiments: ExperimentFormState[],
): ExperimentDefinition[] =>
  experiments.map((experiment) => ({
    name: experiment.name,
    engine: experiment.engine,
    environmentConfig: experiment.environmentConfig,
    controller: experiment.controller,
    controllerConfig: experiment.controllerConfig,
    episodes: typeof experiment.episodes === 'number' ? experiment.episodes : 0,
    reporting: resolveReporting(experiment),
  }))
