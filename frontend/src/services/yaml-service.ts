import yaml from 'js-yaml'
import type { EnvironmentRewardSettings } from '@/components/configurator/environment/env-reward-tab.tsx'
import type { EnvActionSpaceSettings } from '@/components/configurator/environment/env-action-space-tab.tsx'
import type { EnvironmentStateSpaceSettings } from '@/components/configurator/environment/env-state-space-tab.tsx'
import type { EnvironmentGeneralSettings } from '@/components/configurator/environment/env-general-tab.tsx'

export interface EnvironmentConfig {
  generalSettings: EnvironmentGeneralSettings
  stateSpaceSettings: EnvironmentStateSpaceSettings
  actionSpaceSettings: EnvActionSpaceSettings
  rewardSettings: EnvironmentRewardSettings
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
  const variables: Record<string, { type: string; zone: string }> = {}
  const meters: Record<string, string> = {}

  state.variables.forEach((v) => {
    if (v.variableType === 'meter') {
      meters[v.name] = v.meterName
    } else {
      variables[v.name] = {
        type: v.energyPlusType,
        zone: v.zone,
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
    },
    episode: {
      timesteps_per_hour: general.timestepsPerHour,
      period,
    },
  }

  return yaml.dump(doc, { noRefs: true })
}

interface ParsedDoc {
  building_model?: string
  weather_data?: string
  state_space?: {
    variables?: Record<string, { type: string; zone: string }>
    meters?: Record<string, string>
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
    moduleName?: string
    className?: string
    codeParameters?: unknown[]
  }
  episode?: {
    timesteps_per_hour?: number
    period?: number[]
  }
}

export const parseEnvironmentYaml = (yamlStr: string): EnvironmentConfig => {
  const doc = yaml.load(yamlStr) as ParsedDoc

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
  }

  const variables =
    Object.entries(doc.state_space?.variables ?? {}).map(([name, v]) => ({
      name,
      variableType: 'variable' as const,
      energyPlusType: v.type,
      zone: v.zone,
    })) ?? []

  const meters =
    Object.entries(doc.state_space?.meters ?? {}).map(([name, meterName]) => ({
      name,
      variableType: 'meter' as const,
      meterName,
    })) ?? []

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
      .filter(([, value]) => typeof value === 'number') // only keep numeric values
      .map(([key, value]) => ({ key, value: value as number })),
    expression: doc.reward_function?.expression ?? '',
    moduleName: doc.reward_function?.moduleName ?? '',
    className: doc.reward_function?.className ?? '',
    codeParameters: Array.isArray(doc.reward_function?.codeParameters)
      ? (doc.reward_function?.codeParameters as {
          key: string
          value: string
        }[])
      : [],
  }

  return {
    generalSettings,
    stateSpaceSettings,
    actionSpaceSettings,
    rewardSettings,
  }
}
