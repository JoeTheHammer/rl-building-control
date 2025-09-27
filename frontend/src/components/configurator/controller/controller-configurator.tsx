import { useMemo, useState } from 'react'
import CustomPage from '../../shared/page.tsx'
import { Button } from '../../ui/button.tsx'
import { Input } from '../../ui/input.tsx'
import { Checkbox } from '../../ui/checkbox.tsx'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../ui/select.tsx'
import { Save, Code2 } from 'lucide-react'
import StringValueList from '../../shared/string-value-list.tsx'
import CustomEditor from '../../shared/custom-editor.tsx'
import {
  buildControllerYaml,
  parseControllerYaml,
} from '@/services/yaml-service.ts'
import type { KeyValue } from '../../shared/key-value-list.tsx'

type ControllerType = 'reinforcement learning' | 'rule based' | 'custom'

export type ControllerAlgorithm =
  | 'SAC'
  | 'PPO'
  | 'DDPG'
  | 'DQN'
  | 'TD3'
  | 'Recurrent PPO'
  | 'A2C'

export interface ControllerSettings {
  name: string
  type: ControllerType
  algorithm: ControllerAlgorithm | ''
  trainingTimesteps?: number
  reportTraining: boolean
  denormalize: boolean
  tensorboardLogs: boolean
  hpTuning: boolean
  numEpisodes?: number
  numTrials?: number
  hyperparameters: KeyValue[]
}

const controllerTypes: ControllerType[] = [
  'reinforcement learning',
  'rule based',
  'custom',
]

const controllerAlgorithms: ControllerAlgorithm[] = [
  'SAC',
  'PPO',
  'DDPG',
  'DQN',
  'TD3',
  'Recurrent PPO',
  'A2C',
]

const ControllerConfigurator = () => {
  const [settings, setSettings] = useState<ControllerSettings>({
    name: '',
    type: 'reinforcement learning',
    algorithm: '',
    trainingTimesteps: undefined,
    reportTraining: false,
    denormalize: false,
    tensorboardLogs: false,
    hpTuning: false,
    numEpisodes: undefined,
    numTrials: undefined,
    hyperparameters: [{ key: '', value: '' }],
  })

  const [devMode, setDevMode] = useState(false)
  const [editorValue, setEditorValue] = useState('')

  const handleSettingChange = <Field extends keyof ControllerSettings>(
    field: Field,
    value: ControllerSettings[Field],
  ) => {
    setSettings((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  const hyperparameterStrings = useMemo(() => {
    if (!settings.hyperparameters.length) return ['']

    return settings.hyperparameters.map((item) => {
      if (!item.key && !item.value) return ''

      const separator = item.value !== '' ? '=' : ''
      return `${item.key ?? ''}${separator}${item.value ?? ''}`
    })
  }, [settings.hyperparameters])

  const handleHyperparametersChange = (values: string[]) => {
    if (!values.length) {
      handleSettingChange('hyperparameters', [{ key: '', value: '' }])
      return
    }

    const parsed: KeyValue[] = values.map((entry) => {
      const trimmed = entry.trim()

      if (!trimmed.includes('=') && !trimmed.includes(':')) {
        return { key: trimmed, value: '' }
      }

      const separator = trimmed.includes('=') ? '=' : ':'
      const [rawKey, ...rawValue] = trimmed.split(separator)
      return {
        key: rawKey?.trim() ?? '',
        value: rawValue.join(separator).trim(),
      }
    })

    handleSettingChange('hyperparameters', parsed)
  }

  const handleNumberChange = (
    field: 'trainingTimesteps' | 'numEpisodes' | 'numTrials',
    value: string,
  ) => {
    const trimmed = value.trim()
    const parsedValue = trimmed === '' ? undefined : Number(trimmed)
    handleSettingChange(field, Number.isNaN(parsedValue) ? undefined : parsedValue)
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

  return (
    <CustomPage>
      <div className="flex w-full flex-col gap-4 pt-2">
        <div className="grid grid-cols-1 items-center gap-2 md:grid-cols-4">
          <div className="md:col-span-2">
            <span className="text-primary text-md font-bold md:text-xl">
              Controller Configurator
            </span>
          </div>
          <div className="md:col-start-3">
            <Button
              onClick={handleToggleDevMode}
              type="button"
              variant={devMode ? 'default' : 'ghost'}
              className="text-md flex w-full gap-2 border"
            >
              <Code2 className="h-4 w-4" />
              Dev Mode
            </Button>
          </div>
          <div className="md:col-start-4">
            <Button onClick={handleSave} type="button" className="text-md w-full">
              <div className="flex items-center gap-2">
                <Save className="h-4 w-4" />
                <span>Save Configuration</span>
              </div>
            </Button>
          </div>
        </div>

        <hr className="border-t-primary w-full" />

        {devMode ? (
          <CustomEditor
            defaultLanguage="yaml"
            value={editorValue}
            onChange={(value) => setEditorValue(value ?? '')}
            height="600px"
          />
        ) : (
          <div className="flex flex-col gap-8">
            <section className="grid gap-6 lg:grid-cols-2">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-primary" htmlFor="controller-name">
                  Name
                </label>
                <Input
                  id="controller-name"
                  value={settings.name}
                  onChange={(event) => handleSettingChange('name', event.target.value)}
                  placeholder="Enter name"
                />
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-primary">Type</label>
                <Select
                  value={settings.type}
                  onValueChange={(value: ControllerType) =>
                    handleSettingChange('type', value)
                  }
                >
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

              <div className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-primary">Algorithm</label>
                <Select
                  value={settings.algorithm}
                  onValueChange={(value: ControllerAlgorithm) =>
                    handleSettingChange('algorithm', value)
                  }
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select an option" />
                  </SelectTrigger>
                  <SelectContent>
                    {controllerAlgorithms.map((item) => (
                      <SelectItem key={item} value={item}>
                        {item}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-primary" htmlFor="training-timesteps">
                  Training Timesteps
                </label>
                <Input
                  id="training-timesteps"
                  type="number"
                  value={settings.trainingTimesteps ?? ''}
                  onChange={(event) =>
                    handleNumberChange('trainingTimesteps', event.target.value)
                  }
                  placeholder="Enter number"
                />
              </div>
            </section>

            <section className="grid gap-4 lg:grid-cols-2">
              <div className="flex flex-col gap-3">
                <span className="text-primary text-sm font-semibold">
                  Training Options
                </span>
                <label className="flex items-center gap-3 text-sm">
                  <Checkbox
                    checked={settings.reportTraining}
                    onCheckedChange={(checked) =>
                      handleSettingChange('reportTraining', !!checked)
                    }
                  />
                  <span>Report training</span>
                </label>
                <label className="flex items-center gap-3 text-sm">
                  <Checkbox
                    checked={settings.denormalize}
                    onCheckedChange={(checked) =>
                      handleSettingChange('denormalize', !!checked)
                    }
                  />
                  <span>Denormalize</span>
                </label>
                <label className="flex items-center gap-3 text-sm">
                  <Checkbox
                    checked={settings.tensorboardLogs}
                    onCheckedChange={(checked) =>
                      handleSettingChange('tensorboardLogs', !!checked)
                    }
                  />
                  <span>Tensorboard logs</span>
                </label>
              </div>

              <div className="flex flex-col gap-3">
                <label className="flex items-center gap-3 text-sm">
                  <Checkbox
                    checked={settings.hpTuning}
                    onCheckedChange={(checked) =>
                      handleSettingChange('hpTuning', !!checked)
                    }
                  />
                  <span className="text-primary text-sm font-semibold">
                    HP tuning
                  </span>
                </label>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="flex flex-col gap-2">
                    <label
                      className="text-sm font-semibold text-primary"
                      htmlFor="num-episodes"
                    >
                      Num episodes
                    </label>
                    <Input
                      id="num-episodes"
                      type="number"
                      value={settings.numEpisodes ?? ''}
                      onChange={(event) =>
                        handleNumberChange('numEpisodes', event.target.value)
                      }
                      placeholder="Enter number"
                      disabled={!settings.hpTuning}
                    />
                  </div>

                  <div className="flex flex-col gap-2">
                    <label
                      className="text-sm font-semibold text-primary"
                      htmlFor="num-trials"
                    >
                      Num trials
                    </label>
                    <Input
                      id="num-trials"
                      type="number"
                      value={settings.numTrials ?? ''}
                      onChange={(event) =>
                        handleNumberChange('numTrials', event.target.value)
                      }
                      placeholder="Enter number"
                      disabled={!settings.hpTuning}
                    />
                  </div>
                </div>
              </div>
            </section>

            <section className="flex flex-col gap-4">
              <div>
                <h2 className="text-primary text-lg font-semibold">
                  Hyperparameters
                </h2>
                <p className="text-muted-foreground text-sm">
                  Enter parameters as <code>name=value</code> pairs.
                </p>
              </div>
              <StringValueList
                values={hyperparameterStrings}
                onChange={handleHyperparametersChange}
                emptyValueLabel="Parameter"
              />
            </section>
          </div>
        )}
      </div>
    </CustomPage>
  )
}

export default ControllerConfigurator
