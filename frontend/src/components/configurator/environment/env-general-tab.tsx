import { type ChangeEvent, useState } from 'react'

import { DatePicker } from '../../ui/date-picker.tsx'
import { Input } from '../../ui/input.tsx'
import { Button } from '@/components/ui/button.tsx'
import BuildingModelDialog from '@/components/configurator/environment/building-model-dialog.tsx'
import { File, Plus, Trash2 } from 'lucide-react'
import WeatherFileDialog from '@/components/configurator/environment/weather-data-dialog.tsx'
import { Checkbox } from '../../ui/checkbox.tsx'

const getFileName = (value: string) => {
  return value.split(/[/\\]/).pop() || value
}

export interface EnvironmentGeneralSettings {
  buildingModelFile: File | string | null
  weatherDataFile: File | string | null
  startDate: string
  endDate: string
  timestepsPerHour: number | undefined
  weatherVariabilityEnabled: boolean
  weatherVariabilityVariables: WeatherVariabilityVariable[]
}

export interface WeatherVariabilityVariable {
  key: string
  sigma: number
  mu: number
  tau: number
}

interface EnvGeneralTabProps {
  settings: EnvironmentGeneralSettings
  onSettingsChange: (changes: Partial<EnvironmentGeneralSettings>) => void
}

const formatDateForStorage = (date: Date) => {
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

const parseStoredDate = (value: string) => {
  if (!value) return undefined

  const [yearString, monthString, dayString] = value.split('-')
  const year = Number(yearString)
  const month = Number(monthString)
  const day = Number(dayString)

  if (Number.isNaN(year) || Number.isNaN(month) || Number.isNaN(day)) {
    return undefined
  }

  return new Date(year, month - 1, day)
}

const fieldLabelStyles = 'text-sm font-semibold text-primary'
const fieldContainerStyles = 'flex flex-col gap-2'

const EnvGeneralTab = ({ settings, onSettingsChange }: EnvGeneralTabProps) => {
  const [buildingDialogOpen, setBuildingDialogOpen] = useState(false)
  const [weatherDialogOpen, setWeatherDialogOpen] = useState(false)

  const handleStartDateSelect = (date?: Date) => {
    onSettingsChange({ startDate: date ? formatDateForStorage(date) : '' })
  }

  const handleEndDateSelect = (date?: Date) => {
    onSettingsChange({ endDate: date ? formatDateForStorage(date) : '' })
  }

  const handleTimestepsChange = (event: ChangeEvent<HTMLInputElement>) => {
    const { value } = event.target

    if (value === '') {
      onSettingsChange({ timestepsPerHour: undefined })
      return
    }

    const numericValue = Number(value)

    if (!Number.isNaN(numericValue)) {
      onSettingsChange({ timestepsPerHour: numericValue })
    }
  }

  const handleWeatherVariabilityToggle = (checked: boolean) => {
    onSettingsChange({ weatherVariabilityEnabled: checked })
  }

  const handleAddWeatherVariable = () => {
    onSettingsChange({
      weatherVariabilityVariables: [
        ...settings.weatherVariabilityVariables,
        { key: '', sigma: 0, mu: 0, tau: 0 },
      ],
    })
  }

  const handleWeatherVariableChange = (
    index: number,
    field: keyof WeatherVariabilityVariable,
    value: string,
  ) => {
    const updated = settings.weatherVariabilityVariables.map((entry, idx) =>
      idx === index
        ? {
            ...entry,
            [field]:
              field === 'key'
                ? value
                : Number.isNaN(Number(value))
                  ? entry[field]
                  : Number(value),
          }
        : entry,
    )
    onSettingsChange({ weatherVariabilityVariables: updated })
  }

  const handleRemoveWeatherVariable = (index: number) => {
    onSettingsChange({
      weatherVariabilityVariables: settings.weatherVariabilityVariables.filter(
        (_, idx) => idx !== index,
      ),
    })
  }

  const startDate = parseStoredDate(settings.startDate)
  const endDate = parseStoredDate(settings.endDate)

  // helper to display only filename if it's a string path
  const displayName = (file: File | string | null, fallback: string) => {
    if (!file) return fallback
    return typeof file === 'string' ? getFileName(file) : file.name
  }

  return (
    <div className="text-primary flex flex-col gap-4 pt-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        <div className={fieldContainerStyles}>
          <label className={fieldLabelStyles} htmlFor="building-model-input">
            Building Model
          </label>
          <Button type="button" onClick={() => setBuildingDialogOpen(true)}>
            <div className="flex items-center gap-2">
              <File className="h-5 w-5" />
              {displayName(settings.buildingModelFile, 'Select Building Model')}
            </div>
          </Button>
          <BuildingModelDialog
            open={buildingDialogOpen}
            onClose={() => setBuildingDialogOpen(false)}
            onSelect={(file) => onSettingsChange({ buildingModelFile: file })}
          />
          {settings.buildingModelFile && (
            <span className="text-primary/70 truncate text-xs">
              {displayName(settings.buildingModelFile, '')}
            </span>
          )}
        </div>

        <div className={fieldContainerStyles}>
          <label className={fieldLabelStyles} htmlFor="weather-data-input">
            Weather Data
          </label>
          <Button type="button" onClick={() => setWeatherDialogOpen(true)}>
            <div className="flex items-center gap-2">
              <File className="h-5 w-5" />
              {displayName(settings.weatherDataFile, 'Select Weather Folder')}
            </div>
          </Button>
          <WeatherFileDialog
            open={weatherDialogOpen}
            onClose={() => setWeatherDialogOpen(false)}
            onSelect={(folder) => onSettingsChange({ weatherDataFile: folder })}
          />
          {settings.weatherDataFile && (
            <span className="text-primary/70 truncate text-xs">
              {displayName(settings.weatherDataFile, '')}
            </span>
          )}
        </div>

        <div className={fieldContainerStyles}>
          <label className={fieldLabelStyles} htmlFor="start-date-input">
            Start Date Episode
          </label>
          <DatePicker
            id="start-date-input"
            date={startDate}
            onDateChange={handleStartDateSelect}
            placeholder="Select start date"
          />
        </div>

        <div className={fieldContainerStyles}>
          <label className={fieldLabelStyles} htmlFor="end-date-input">
            End Date Episode
          </label>
          <DatePicker
            id="end-date-input"
            date={endDate}
            onDateChange={handleEndDateSelect}
            placeholder="Select end date"
          />
        </div>

        <div className={fieldContainerStyles}>
          <label className={fieldLabelStyles} htmlFor="timesteps-input">
            Timesteps per hour
          </label>
          <Input
            id="timesteps-input"
            type="number"
            min={1}
            value={settings.timestepsPerHour ?? 4}
            onChange={handleTimestepsChange}
          />
        </div>
      </div>

      <div className="border-input flex flex-col gap-4 rounded-lg border p-4">
        <label className="flex items-center gap-3">
          <Checkbox
            checked={settings.weatherVariabilityEnabled}
            onCheckedChange={(checked: boolean) =>
              handleWeatherVariabilityToggle(checked)
            }
          />
          <span className={fieldLabelStyles}>Weather Variability</span>
        </label>
        <div className="flex flex-col gap-3">
          {settings.weatherVariabilityVariables.map((entry, index) => (
            <div
              key={`weather-var-${index}`}
              className="grid gap-3 md:grid-cols-5"
            >
              <div className="flex flex-col gap-1">
                <label className="text-primary text-xs font-semibold">
                  Variable key
                </label>
                <Input
                  value={entry.key}
                  onChange={(event) =>
                    handleWeatherVariableChange(
                      index,
                      'key',
                      event.target.value,
                    )
                  }
                  placeholder="Variable key"
                  disabled={!settings.weatherVariabilityEnabled}
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-primary text-xs font-semibold">
                  Sigma
                </label>
                <Input
                  type="number"
                  value={entry.sigma}
                  onChange={(event) =>
                    handleWeatherVariableChange(
                      index,
                      'sigma',
                      event.target.value,
                    )
                  }
                  placeholder="Sigma"
                  disabled={!settings.weatherVariabilityEnabled}
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-primary text-xs font-semibold">Mu</label>
                <Input
                  type="number"
                  value={entry.mu}
                  onChange={(event) =>
                    handleWeatherVariableChange(index, 'mu', event.target.value)
                  }
                  placeholder="Mu"
                  disabled={!settings.weatherVariabilityEnabled}
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-primary text-xs font-semibold">
                  Tau
                </label>
                <Input
                  type="number"
                  value={entry.tau}
                  onChange={(event) =>
                    handleWeatherVariableChange(
                      index,
                      'tau',
                      event.target.value,
                    )
                  }
                  placeholder="Tau"
                  disabled={!settings.weatherVariabilityEnabled}
                />
              </div>

              <div className="flex items-end">
                <Button
                  size="icon"
                  type="button"
                  onClick={() => handleRemoveWeatherVariable(index)}
                  disabled={!settings.weatherVariabilityEnabled}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
          <Button
            onClick={handleAddWeatherVariable}
            type="button"
            className="w-fit"
            disabled={!settings.weatherVariabilityEnabled}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Variable
          </Button>
        </div>
      </div>
    </div>
  )
}

export default EnvGeneralTab
