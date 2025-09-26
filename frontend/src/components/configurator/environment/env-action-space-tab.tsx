import { type ChangeEvent } from 'react'
import { Trash2, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import NumericValueList from '@/components/shared/numeric-value-list'

export interface Actuator {
  actuatorName: string
  component: string
  controlType: string
  actuatorKey: string
  type: 'continuous' | 'discrete'
  mode?: 'values' | 'range'
  valueList: number[]
  min?: number
  max?: number
  stepSize?: number
}

export interface EnvActionSpaceSettings {
  actuators: Actuator[]
}

export interface EnvActionSpaceTabProps {
  settings: EnvActionSpaceSettings
  onSettingsChange: (changes: Partial<EnvActionSpaceSettings>) => void
}

const fieldLabelStyles = 'text-sm font-semibold text-primary'
const fieldContainerStyles = 'flex flex-col gap-1'

const EnvActionSpaceTab = ({
  settings,
  onSettingsChange,
}: EnvActionSpaceTabProps) => {
  const handleActuatorChange = <K extends keyof Actuator>(
    index: number,
    field: K,
    value: Actuator[K],
  ) => {
    const updated = settings.actuators.map((a, i) =>
      i === index ? { ...a, [field]: value } : a,
    )
    onSettingsChange({ actuators: updated })
  }

  const handleAddActuator = () => {
    const updated = [
      ...settings.actuators,
      {
        actuatorName: '',
        component: '',
        controlType: '',
        actuatorKey: '',
        type: 'continuous',
        mode: undefined,
        valueList: [],
        min: undefined,
        max: undefined,
        stepSize: undefined,
      },
    ]
    onSettingsChange({ actuators: updated as Actuator[] })
  }

  const handleRemoveActuator = (index: number) => {
    onSettingsChange({
      actuators: settings.actuators.filter((_, i) => i !== index),
    })
  }

  return (
    <div className="text-primary flex flex-col gap-6 pt-4">
      {settings.actuators.map((actuator, index) => (
        <div
          key={index}
          className="bg-muted/40 border-border flex flex-col gap-6 rounded-xl border p-4 shadow-sm"
        >
          {/* 8-column grid */}
          <div className="grid grid-cols-8 gap-4">
            {/* Top row */}
            <div className={`${fieldContainerStyles} col-span-2`}>
              <label className={fieldLabelStyles}>Actuator Name</label>
              <Input
                value={actuator.actuatorName}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  handleActuatorChange(index, 'actuatorName', e.target.value)
                }
              />
            </div>
            <div className={`${fieldContainerStyles} col-span-2`}>
              <label className={fieldLabelStyles}>Component</label>
              <Input
                value={actuator.component}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  handleActuatorChange(index, 'component', e.target.value)
                }
              />
            </div>
            <div className={`${fieldContainerStyles} col-span-2`}>
              <label className={fieldLabelStyles}>Control Type</label>
              <Input
                value={actuator.controlType}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  handleActuatorChange(index, 'controlType', e.target.value)
                }
              />
            </div>
            <div className={`${fieldContainerStyles} col-span-2`}>
              <label className={fieldLabelStyles}>Actuator Key</label>
              <Input
                value={actuator.actuatorKey}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  handleActuatorChange(index, 'actuatorKey', e.target.value)
                }
              />
            </div>

            {/* Type always under Actuator Name */}
            <div className={`${fieldContainerStyles} col-span-1`}>
              <label className={fieldLabelStyles}>Type</label>
              <Select
                value={actuator.type}
                onValueChange={(value) =>
                  handleActuatorChange(
                    index,
                    'type',
                    value as 'continuous' | 'discrete',
                  )
                }
              >
                <SelectTrigger className="bg-background w-full">
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent className="bg-background">
                  <SelectItem value="continuous">Continuous</SelectItem>
                  <SelectItem value="discrete">Discrete</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Continuous → Min/Max next to Type */}
            {actuator.type === 'continuous' && (
              <>
                <div className={`${fieldContainerStyles} col-span`}>
                  <label className={fieldLabelStyles}>Min</label>
                  <Input
                    type="number"
                    value={actuator.min ?? ''}
                    onChange={(e: ChangeEvent<HTMLInputElement>) =>
                      handleActuatorChange(
                        index,
                        'min',
                        e.target.value ? Number(e.target.value) : undefined,
                      )
                    }
                  />
                </div>
                <div className={`${fieldContainerStyles} col-span`}>
                  <label className={fieldLabelStyles}>Max</label>
                  <Input
                    type="number"
                    value={actuator.max ?? ''}
                    onChange={(e: ChangeEvent<HTMLInputElement>) =>
                      handleActuatorChange(
                        index,
                        'max',
                        e.target.value ? Number(e.target.value) : undefined,
                      )
                    }
                  />
                </div>
              </>
            )}

            {/* Discrete → Mode under Component */}
            {actuator.type === 'discrete' && (
              <div className={fieldContainerStyles}>
                <label className={fieldLabelStyles}>Mode</label>
                <Select
                  value={actuator.mode}
                  onValueChange={(value) =>
                    handleActuatorChange(
                      index,
                      'mode',
                      value as 'values' | 'range',
                    )
                  }
                >
                  <SelectTrigger className="bg-background w-full">
                    <SelectValue placeholder="Select mode" />
                  </SelectTrigger>
                  <SelectContent className="bg-background">
                    <SelectItem value="values">Values</SelectItem>
                    <SelectItem value="range">Range</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Discrete: Values → Full width row */}
            {actuator.type === 'discrete' && actuator.mode === 'values' && (
              <div className="col-span-8 flex flex-col gap-2">
                <label className={fieldLabelStyles}>Values</label>
                <NumericValueList
                  values={actuator.valueList}
                  onChange={(vals) =>
                    handleActuatorChange(index, 'valueList', vals)
                  }
                />
              </div>
            )}

            {/* Discrete: Range → Min, Max, StepSize in fixed slots */}
            {actuator.type === 'discrete' && actuator.mode === 'range' && (
              <>
                <div className={fieldContainerStyles}>
                  <label className={fieldLabelStyles}>Min</label>
                  <Input
                    type="number"
                    value={actuator.min ?? ''}
                    onChange={(e: ChangeEvent<HTMLInputElement>) =>
                      handleActuatorChange(
                        index,
                        'min',
                        e.target.value ? Number(e.target.value) : undefined,
                      )
                    }
                  />
                </div>
                <div className={`${fieldContainerStyles}`}>
                  <label className={fieldLabelStyles}>Max</label>
                  <Input
                    type="number"
                    value={actuator.max ?? ''}
                    onChange={(e: ChangeEvent<HTMLInputElement>) =>
                      handleActuatorChange(
                        index,
                        'max',
                        e.target.value ? Number(e.target.value) : undefined,
                      )
                    }
                  />
                </div>
                <div className={fieldContainerStyles}>
                  <label className={fieldLabelStyles}>Step Size</label>
                  <Input
                    type="number"
                    value={actuator.stepSize ?? ''}
                    onChange={(e: ChangeEvent<HTMLInputElement>) =>
                      handleActuatorChange(
                        index,
                        'stepSize',
                        e.target.value ? Number(e.target.value) : undefined,
                      )
                    }
                  />
                </div>
              </>
            )}
            <div className="col-start-8 flex h-full items-center justify-end">
              <Button size="icon" onClick={() => handleRemoveActuator(index)}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      ))}

      <Button onClick={handleAddActuator} type="button" className="mt-2 w-fit">
        <Plus className="mr-2 h-4 w-4" />
        Add Actuator
      </Button>
    </div>
  )
}

export default EnvActionSpaceTab
