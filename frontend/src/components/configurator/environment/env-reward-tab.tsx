import { useCallback } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../ui/select.tsx'
import StringValueList from '@/components/shared/string-value-list'
import CustomEditor from '@/components/shared/custom-editor.tsx'
import NumericalKeyValueList, {
  type NumericalKeyValue,
} from '@/components/shared/numerical-key-value-list.tsx'

export type EnvironmentRewardType = 'expression' | 'code based'

export interface EnvironmentRewardSettings {
  type: EnvironmentRewardType
  variables: string[]
  parameters: NumericalKeyValue[]
  expression: string
}

interface EnvRewardTabProps {
  settings: EnvironmentRewardSettings
  onSettingsChange: (changes: Partial<EnvironmentRewardSettings>) => void
}

const sectionTitleStyle = 'text-lg font-semibold text-primary'
const cardStyle =
  'border-input flex h-full flex-col gap-4 rounded-lg border bg-card p-4 shadow-sm'

const EnvRewardTab = ({ settings, onSettingsChange }: EnvRewardTabProps) => {
  const handleTypeChange = useCallback(
    (value: EnvironmentRewardType) => {
      onSettingsChange({ type: value })
    },
    [onSettingsChange],
  )

  const handleVariablesChange = useCallback(
    (variables: string[]) => {
      onSettingsChange({ variables })
    },
    [onSettingsChange],
  )

  const handleParametersChange = useCallback(
    (parameters: NumericalKeyValue[]) => {
      onSettingsChange({ parameters })
    },
    [onSettingsChange],
  )

  const handleExpressionChange = useCallback(
    (value: string | undefined) => {
      onSettingsChange({ expression: value ?? '' })
    },
    [onSettingsChange],
  )

  // known words = variables + parameter keys
  const knownWords = [
    ...settings.variables,
    ...settings.parameters.map((p) => p.key),
  ]

  return (
    <div className="text-primary flex flex-col gap-8 pt-6">
      {/* Reward type select */}
      <div className="flex flex-col gap-2">
        <label htmlFor="reward-type" className="text-sm font-semibold">
          Type
        </label>
        <Select
          value={settings.type}
          onValueChange={(value) =>
            handleTypeChange(value as EnvironmentRewardType)
          }
        >
          <SelectTrigger id="reward-type" className="w-[310px]">
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent className="bg-background">
            <SelectItem value="expression">expression</SelectItem>
            <SelectItem value="code based" disabled>
              code based
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className={cardStyle}>
          <h3 className={sectionTitleStyle}>Variables</h3>
          <StringValueList
            values={settings.variables}
            onChange={handleVariablesChange}
            emptyValueLabel="Variable"
          />
        </div>

        <div className={cardStyle}>
          <h3 className={sectionTitleStyle}>Parameters</h3>
          <NumericalKeyValueList
            values={settings.parameters}
            onChange={handleParametersChange}
            emptyKeyLabel="Parameter"
          />
        </div>
      </div>

      {settings.type === 'expression' && (
        <section className="flex flex-col gap-4">
          <h3 className={sectionTitleStyle}>Expression</h3>
          <div className="border-input overflow-hidden rounded-lg border shadow-sm">
            <CustomEditor
              height="320px"
              defaultLanguage="python"
              theme="vs-light"
              value={settings.expression}
              onChange={handleExpressionChange}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                automaticLayout: true,
              }}
              knownWords={knownWords}
            />
          </div>
        </section>
      )}
    </div>
  )
}

export default EnvRewardTab
