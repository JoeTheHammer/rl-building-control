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
import KeyValueList, { type KeyValue } from '@/components/shared/key-value-list'
import { Input } from '../../ui/input.tsx'

export type EnvironmentRewardType = 'expression' | 'code based'

export interface EnvironmentRewardSettings {
  type: EnvironmentRewardType
  variables: string[]
  parameters: NumericalKeyValue[]
  expression: string
  moduleName?: string
  className?: string
  codeParameters?: KeyValue[]
}

interface EnvRewardTabProps {
  settings: EnvironmentRewardSettings
  onSettingsChange: (changes: Partial<EnvironmentRewardSettings>) => void
}

const sectionTitleStyle = 'text-lg font-semibold text-primary'
const cardStyle =
  'border-input flex h-full flex-col gap-4 rounded-lg border bg-card p-4 shadow-sm'

const fieldLabelStyles = 'text-sm font-semibold text-primary'
const fieldContainerStyles = 'flex flex-col gap-2'

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

  const handleModuleNameChange = useCallback(
    (value: string) => {
      onSettingsChange({ moduleName: value })
    },
    [onSettingsChange],
  )

  const handleClassNameChange = useCallback(
    (value: string) => {
      onSettingsChange({ className: value })
    },
    [onSettingsChange],
  )

  const handleCodeParametersChange = useCallback(
    (params: KeyValue[]) => {
      onSettingsChange({ codeParameters: params })
    },
    [onSettingsChange],
  )

  const knownWords = [
    ...settings.variables,
    ...settings.parameters.map((p) => p.key),
  ]

  return (
    <div className="text-primary flex flex-col gap-6 pt-4">
      {/* Reward type select */}
      <div className={fieldContainerStyles}>
        <label htmlFor="reward-type" className={fieldLabelStyles}>
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
            <SelectItem value="code based">code based</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Expression mode */}
      {settings.type === 'expression' && (
        <>
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

          <section className="flex flex-col gap-1">
            <h3 className={sectionTitleStyle}>Expression</h3>
            <div className="border-input overflow-hidden rounded-lg border shadow-sm">
              <CustomEditor
                height="250px"
                defaultLanguage="plaintext"
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
        </>
      )}

      {/* Code based mode */}
      {settings.type === 'code based' && (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className={fieldContainerStyles}>
            <label htmlFor="reward-module" className={fieldLabelStyles}>
              Module
            </label>
            <Input
              id="reward-module"
              value={settings.moduleName ?? ''}
              onChange={(e) => handleModuleNameChange(e.target.value)}
              placeholder="Module name"
            />
          </div>

          <div className={fieldContainerStyles}>
            <label htmlFor="reward-class" className={fieldLabelStyles}>
              Class
            </label>
            <Input
              id="reward-class"
              value={settings.className ?? ''}
              onChange={(e) => handleClassNameChange(e.target.value)}
              placeholder="Class name"
            />
          </div>

          <div className="lg:col-span-2">
            <h3 className={sectionTitleStyle}>Parameters</h3>
            <KeyValueList
              values={settings.codeParameters ?? []}
              onChange={handleCodeParametersChange}
              emptyKeyLabel="Parameter"
              emptyValueLabel="Value"
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default EnvRewardTab
