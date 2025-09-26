import yaml from 'js-yaml'
import type { EnvironmentRewardSettings } from '@/components/configurator/environment/env-reward-tab.tsx'
import type { EnvActionSpaceSettings } from '@/components/configurator/environment/env-action-space-tab.tsx'
import type { EnvironmentStateSpaceSettings } from '@/components/configurator/environment/env-state-space-tab.tsx'
import type { EnvironmentGeneralSettings } from '@/components/configurator/environment/env-general-tab.tsx'

// helper to normalize file inputs to strings
const normalizeFile = (
  file: File | string | null | undefined,
): string | null => {
  if (!file) return null
  if (typeof file === 'string') return file
  if (file instanceof File) return file.name
  return null
}

// helper to make inline arrays
const inlineArray = (arr: unknown[]) => {
  const node: any = arr
  node.tag = '!!seq'
  node.flow = true
  return node
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
    return [d.getDate(), d.getMonth() + 1, d.getFullYear()]
  }
  const start = parseDate(general.startDate)
  const end = parseDate(general.endDate)
  const period = [...start, ...end]

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
                range: inlineArray([a.min, a.max]),
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
                range: inlineArray([a.min, a.max]),
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
                values: inlineArray(a.valueList),
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
      variables: inlineArray(reward.variables),
      expression: reward.expression,
      params: Object.fromEntries(
        reward.parameters.map((p) => [p.key, p.value]),
      ),
    },
    episode: {
      timesteps_per_hour: general.timestepsPerHour,
      period: inlineArray(period),
    },
  }

  return yaml.dump(doc, { noRefs: true })
}
