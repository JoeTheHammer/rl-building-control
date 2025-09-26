import type { ChangeEvent } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../ui/select.tsx'
import { Button } from '../../ui/button.tsx'
import { Input } from '../../ui/input.tsx'
import { Checkbox } from '../../ui/checkbox.tsx'
import { cn } from '../../../lib/utils.ts'

export interface TimeFeatureSetting {
  included: boolean
  cyclic: boolean
}

export type TimeFeatureKey =
  | 'dayOfMonth'
  | 'dayOfWeek'
  | 'hour'
  | 'minute'
  | 'month'

export interface EnvironmentStateSpaceSettings {
  addTimeInfo: boolean
  dayOfMonth: TimeFeatureSetting
  dayOfWeek: TimeFeatureSetting
  hour: TimeFeatureSetting
  minute: TimeFeatureSetting
  month: TimeFeatureSetting
  variables: {
    name: string
    variableType: 'variable' | 'meter'
    energyPlusType: string
    zone: string
  }[]
}

export interface EnvStateSpaceTabProps {
  settings: EnvironmentStateSpaceSettings
  onSettingsChange: (changes: Partial<EnvironmentStateSpaceSettings>) => void
}

const fieldLabelStyles = 'text-sm font-semibold text-primary'
const fieldContainerStyles = 'flex flex-col gap-2'

const timeFeatureLabels: Record<TimeFeatureKey, string> = {
  dayOfMonth: 'Day of month',
  dayOfWeek: 'Day of week',
  hour: 'Hour',
  minute: 'Minute',
  month: 'Month',
}

const EnvStateSpaceTab = ({
  settings,
  onSettingsChange,
}: EnvStateSpaceTabProps) => {
  const handleAddTimeInfoChange = (checked: boolean) => {
    onSettingsChange({ addTimeInfo: checked })
  }

  const updateTimeFeature = (
    key: TimeFeatureKey,
    changes: Partial<TimeFeatureSetting>,
  ) => {
    onSettingsChange({
      [key]: { ...settings[key], ...changes },
    } as Partial<EnvironmentStateSpaceSettings>)
  }

  const handleVariableFieldChange = <
    Field extends 'name' | 'variableType' | 'energyPlusType' | 'zone',
  >(
    index: number,
    field: Field,
    value: EnvironmentStateSpaceSettings['variables'][number][Field],
  ) => {
    const updatedVariables = settings.variables.map(
      (variable, variableIndex) =>
        variableIndex === index ? { ...variable, [field]: value } : variable,
    )
    onSettingsChange({ variables: updatedVariables })
  }

  const handleRemoveVariable = (index: number) => {
    const updatedVariables = settings.variables.filter(
      (_, variableIndex) => variableIndex !== index,
    )
    onSettingsChange({ variables: updatedVariables })
  }

  const handleAddVariable = () => {
    const updatedVariables = [
      ...settings.variables,
      { name: '', variableType: 'variable', energyPlusType: '', zone: '' },
    ]

    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-expect-error
    onSettingsChange({ variables: updatedVariables })
  }

  return (
    <div className="text-primary flex flex-col gap-8 pt-4">
      <section className="flex flex-col gap-4">
        <label className="flex items-center gap-3">
          <Checkbox
            checked={settings.addTimeInfo}
            onCheckedChange={(checked: boolean) =>
              handleAddTimeInfoChange(checked)
            }
          />
          <span className={fieldLabelStyles}>Add Time Information</span>
        </label>

        {settings.addTimeInfo && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {(Object.keys(timeFeatureLabels) as TimeFeatureKey[]).map((key) => {
              const feature = settings[key]

              return (
                <div
                  key={key}
                  className="border-input text-primary flex flex-col gap-3 rounded-lg border p-4"
                >
                  <h3 className="text-sm font-semibold capitalize">
                    {timeFeatureLabels[key]}
                  </h3>
                  <label className="flex items-center gap-2 text-sm">
                    <Checkbox
                      checked={feature.included}
                      onCheckedChange={(checked) =>
                        updateTimeFeature(key, { included: !!checked })
                      }
                    />
                    <span>Included</span>
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <Checkbox
                      checked={feature.cyclic}
                      onCheckedChange={(checked) =>
                        updateTimeFeature(key, { cyclic: !!checked })
                      }
                      disabled={!feature.included}
                    />
                    <span>Cyclic</span>
                  </label>
                </div>
              )
            })}
          </div>
        )}
      </section>

      <section className="flex flex-col gap-4">
        <h2 className="text-primary text-lg font-semibold">Variables</h2>
        <div className="flex flex-col gap-4">
          {settings.variables.map((variable, index) => (
            <div
              key={`${variable.name}-${index}`}
              className="border-input flex flex-col gap-4 rounded-lg border p-4 shadow-md"
            >
              <div className="grid items-end gap-4 md:grid-cols-[repeat(4,minmax(0,1fr))_auto]">
                <div className={fieldContainerStyles}>
                  <label
                    className={fieldLabelStyles}
                    htmlFor={`variable-name-${index}`}
                  >
                    Variable Name
                  </label>
                  <Input
                    id={`variable-name-${index}`}
                    value={variable.name}
                    onChange={(event: ChangeEvent<HTMLInputElement>) =>
                      handleVariableFieldChange(
                        index,
                        'name',
                        event.target.value,
                      )
                    }
                    placeholder="Enter variable name"
                  />
                </div>

                <div className={cn(fieldContainerStyles, 'w-full')}>
                  <label className={fieldLabelStyles}>Type</label>
                  <Select
                    value={variable.variableType}
                    onValueChange={(value) =>
                      handleVariableFieldChange(
                        index,
                        'variableType',
                        value as 'variable' | 'meter',
                      )
                    }
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue
                        placeholder="Select type"
                        className="w-full"
                      />
                    </SelectTrigger>
                    <SelectContent className="bg-background">
                      <SelectItem value="variable">Variable</SelectItem>
                      <SelectItem value="meter">Meter</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className={fieldContainerStyles}>
                  <label
                    className={fieldLabelStyles}
                    htmlFor={`variable-energy-${index}`}
                  >
                    EnergyPlus Type
                  </label>
                  <Input
                    id={`variable-energy-${index}`}
                    value={variable.energyPlusType}
                    onChange={(event: ChangeEvent<HTMLInputElement>) =>
                      handleVariableFieldChange(
                        index,
                        'energyPlusType',
                        event.target.value,
                      )
                    }
                    placeholder="Enter EnergyPlus type"
                  />
                </div>

                <div className={fieldContainerStyles}>
                  <label
                    className={fieldLabelStyles}
                    htmlFor={`variable-zone-${index}`}
                  >
                    Zone
                  </label>
                  <Input
                    id={`variable-zone-${index}`}
                    value={variable.zone}
                    onChange={(event: ChangeEvent<HTMLInputElement>) =>
                      handleVariableFieldChange(
                        index,
                        'zone',
                        event.target.value,
                      )
                    }
                    placeholder="Enter zone"
                  />
                </div>

                <div className="flex justify-end">
                  <Button
                    size="icon"
                    onClick={() => handleRemoveVariable(index)}
                    aria-label="Remove variable"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
          <div>
            <Button type="button" onClick={handleAddVariable}>
              <Plus className="mr-2 h-4 w-4" />
              Add
            </Button>
          </div>
        </div>
      </section>
    </div>
  )
}

export default EnvStateSpaceTab
