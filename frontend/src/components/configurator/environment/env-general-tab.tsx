import { type ChangeEvent, useState } from 'react'

import { DatePicker } from '../../ui/date-picker.tsx'
import { Input } from '../../ui/input.tsx'
import { Button } from '@/components/ui/button.tsx'
import BuildingModelDialog from '@/components/configurator/environment/building-model-dialog.tsx'
import { File } from 'lucide-react'
import WeatherFileDialog from '@/components/configurator/environment/weather-data-dialog.tsx'

const getFileName = (value: string) => {
  return value.split(/[/\\]/).pop() || value
}

export interface EnvironmentGeneralSettings {
  buildingModelFile: File | string | null
  weatherDataFile: File | string | null
  startDate: string
  endDate: string
  timestepsPerHour: number | undefined
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
    </div>
  )
}

export default EnvGeneralTab
