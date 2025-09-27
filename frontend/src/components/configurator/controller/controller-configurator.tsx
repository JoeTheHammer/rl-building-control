import { useState, useRef } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../ui/select.tsx'
import type { KeyValue } from '../../shared/key-value-list.tsx'
import CustomEditor from '../../shared/custom-editor.tsx'
import {
  buildControllerYaml,
  parseControllerYaml,
} from '@/services/yaml-service.ts'
import { getDefaultControllerHyperparameters } from './controller-defaults.ts'
import ControllerToolbar from './controller-toolbar.tsx'
import ReinforcementLearningSection from './controller-reinforcement-learning-section.tsx'
import RuleBasedSection from './controller-rule-based-section.tsx'
import CustomSection from './controller-custom-section.tsx'
import type {
  ControllerRule,
  ControllerSettings,
  ControllerType,
} from './controller-types.ts'

const controllerTypes: ControllerType[] = [
  'reinforcement learning',
  'rule based',
  'custom',
]

const createEmptyRule = (): ControllerRule => ({ condition: '', action: '' })

const ControllerConfigurator = () => {
  const [settings, setSettings] = useState<ControllerSettings>({
    type: 'reinforcement learning',
    trainingTimesteps: undefined,
    reportTraining: false,
    denormalize: false,
    tensorboardLogs: false,
    hpTuning: false,
    numEpisodes: undefined,
    numTrials: undefined,
    hyperparameters: getDefaultControllerHyperparameters(),
    customVariables: [],
    stateSpace: [],
    rules: [createEmptyRule()],
    customModule: '',
    customClassName: '',
    initArguments: [],
  })

  const [devMode, setDevMode] = useState(false)
  const [editorValue, setEditorValue] = useState('')
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const updateSettings = <Field extends keyof ControllerSettings>(
    field: Field,
    value: ControllerSettings[Field],
  ) => {
    setSettings((previous) => ({
      ...previous,
      [field]: value,
    }))
  }

  const handleNumberChange = (
    field: 'trainingTimesteps' | 'numEpisodes' | 'numTrials',
    value: string,
  ) => {
    const trimmed = value.trim()
    const parsedValue = trimmed === '' ? undefined : Number(trimmed)
    updateSettings(field, Number.isNaN(parsedValue) ? undefined : parsedValue)
  }

  const handleBooleanChange = (
    field: 'reportTraining' | 'denormalize' | 'tensorboardLogs' | 'hpTuning',
    value: boolean,
  ) => {
    updateSettings(field, value)
  }

  const handleHyperparametersChange = (values: KeyValue[]) => {
    updateSettings('hyperparameters', values)
  }

  const handleTypeChange = (value: ControllerType) => {
    setSettings((previous) => ({
      ...previous,
      type: value,
      rules:
        value === 'rule based' && previous.rules.length === 0
          ? [createEmptyRule()]
          : previous.rules,
    }))
  }

  const handleCustomVariablesChange = (values: KeyValue[]) => {
    updateSettings('customVariables', values)
  }

  const handleStateSpaceChange = (values: string[]) => {
    updateSettings('stateSpace', values)
  }

  const handleCustomModuleChange = (value: string) => {
    updateSettings('customModule', value)
  }

  const handleCustomClassNameChange = (value: string) => {
    updateSettings('customClassName', value)
  }

  const handleInitArgumentsChange = (values: KeyValue[]) => {
    updateSettings('initArguments', values)
  }

  const handleRuleChange = (
    index: number,
    field: keyof ControllerRule,
    value: string,
  ) => {
    setSettings((previous) => ({
      ...previous,
      rules: previous.rules.map((rule, ruleIndex) =>
        ruleIndex === index ? { ...rule, [field]: value } : rule,
      ),
    }))
  }

  const handleAddRule = () => {
    setSettings((previous) => ({
      ...previous,
      rules: [...previous.rules, createEmptyRule()],
    }))
  }

  const handleRemoveRule = (index: number) => {
    setSettings((previous) => ({
      ...previous,
      rules: previous.rules.filter((_, ruleIndex) => ruleIndex !== index),
    }))
  }

  const handleSave = () => {
    if (devMode) {
      try {
        const parsed = parseControllerYaml(editorValue)
        setSettings(parsed)
        console.log('Saved from Dev Mode', parsed)
      } catch (error) {
        console.error('Invalid YAML. Could not save.', error)
      }
    } else {
      const yamlString = buildControllerYaml(settings)
      console.log('Saving controller configuration', settings)
      console.log(yamlString)
      console.log(parseControllerYaml(yamlString))
    }
  }

  const handleToggleDevMode = () => {
    if (!devMode) {
      const yamlString = buildControllerYaml(settings)
      setEditorValue(yamlString)
      setDevMode(true)
    } else {
      try {
        const parsed = parseControllerYaml(editorValue)
        setSettings(parsed)
      } catch (error) {
        console.error('Invalid YAML, keeping previous state', error)
      }
      setDevMode(false)
    }
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const text = await file.text()
      const parsed = parseControllerYaml(text)
      setSettings(parsed)
      console.log('Uploaded and parsed controller YAML', parsed)
    } catch (error) {
      console.error('Failed to parse uploaded YAML file', error)
    } finally {
      e.target.value = ''
    }
  }

  return (
    <ControllerToolbar
      devMode={devMode}
      onToggleDevMode={handleToggleDevMode}
      onSave={handleSave}
      onUpload={handleUploadClick}
      fileInputRef={fileInputRef}
      onFileChange={handleFileChange}
    >
      {devMode ? (
        <CustomEditor
          defaultLanguage="yaml"
          value={editorValue}
          onChange={(value) => setEditorValue(value ?? '')}
          height="600px"
        />
      ) : (
        <div className="flex flex-col gap-8">
          <section className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <div className="flex flex-col gap-2">
              <label className="text-primary text-sm font-semibold">Type</label>
              <Select value={settings.type} onValueChange={handleTypeChange}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select an option" />
                </SelectTrigger>
                <SelectContent>
                  {controllerTypes.map((item) => (
                    <SelectItem key={item} value={item}>
                      {item.charAt(0).toUpperCase() + item.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </section>

          {settings.type === 'rule based' ? (
            <RuleBasedSection
              customVariables={settings.customVariables}
              onCustomVariablesChange={handleCustomVariablesChange}
              stateSpace={settings.stateSpace}
              onStateSpaceChange={handleStateSpaceChange}
              rules={settings.rules}
              onRuleChange={handleRuleChange}
              onAddRule={handleAddRule}
              onRemoveRule={handleRemoveRule}
            />
          ) : settings.type === 'custom' ? (
            <CustomSection
              modulePath={settings.customModule}
              className={settings.customClassName}
              initArguments={settings.initArguments}
              onModuleChange={handleCustomModuleChange}
              onClassNameChange={handleCustomClassNameChange}
              onInitArgumentsChange={handleInitArgumentsChange}
            />
          ) : (
            <ReinforcementLearningSection
              settings={settings}
              onNumberChange={handleNumberChange}
              onBooleanChange={handleBooleanChange}
              onHyperparametersChange={handleHyperparametersChange}
            />
          )}
        </div>
      )}
    </ControllerToolbar>
  )
}

export default ControllerConfigurator
