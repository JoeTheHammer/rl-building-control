import { useMemo, useRef, useState } from 'react'
import type { ChangeEvent } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import CustomEditor from '../../shared/custom-editor.tsx'
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
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card.tsx'
import { Badge } from '@/components/ui/badge'

import ExperimentToolbar from './experiment-toolbar.tsx'
import ExperimentSaveDialog from './experiment-save-dialog.tsx'
import ExperimentConfigDialog from './experiment-config-dialog.tsx'
import EnvironmentConfigDialog from '../environment/environment-config-dialog.tsx'
import ControllerConfigDialog from '../controller/controller-config-dialog.tsx'
import {
  buildExperimentYaml,
  parseExperimentYaml,
  type ExperimentFormState,
} from '@/services/yaml-service.ts'
import { fetchExperimentConfig } from '@/services/experiment-service.ts'

interface ControllerOption {
  key: string
  name: string
}

const controllerOptions: ControllerOption[] = [
  {
    key: 'rule-based',
    name: 'Rule Based',
  },
  {
    key: 'custom',
    name: 'Custom',
  },
  {
    key: 'sac',
    name: 'SAC',
  },
  {
    key: 'ppo',
    name: 'PPO',
  },
  {
    key: 'recurrent-ppo',
    name: 'Recurrent PPO',
  },
  {
    key: 'a2c',
    name: 'A2C',
  },
  {
    key: 'ddpg',
    name: 'DDPG',
  },
  {
    key: 'td3',
    name: 'TD3',
  },
  {
    key: 'dqn',
    name: 'DQN',
  },
]

const createDefaultExperiment = (): ExperimentFormState => ({
  name: '',
  engine: 'sinergym',
  environmentConfig: '',
  controller: 'ppo',
  controllerConfig: '',
  episodes: 1,
  reporting: {
    plots: false,
    denormalizeState: false,
    export: false,
  },
  reportingEnabled: false,
})

const ExperimentConfigurator = () => {
  const [experiments, setExperiments] = useState<ExperimentFormState[]>([
    createDefaultExperiment(),
  ])
  const [devMode, setDevMode] = useState(false)
  const [editorValue, setEditorValue] = useState('')
  const [saveDialogOpen, setSaveDialogOpen] = useState(false)
  const [configDialogOpen, setConfigDialogOpen] = useState(false)
  const [environmentDialogIndex, setEnvironmentDialogIndex] = useState<
    number | null
  >(null)
  const [controllerDialogIndex, setControllerDialogIndex] = useState<
    number | null
  >(null)
  const [openedFile, setOpenedFile] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const resolvedYaml = useMemo(
    () => (devMode ? editorValue : buildExperimentYaml(experiments)),
    [devMode, editorValue, experiments],
  )

  const updateExperiment = <Field extends keyof ExperimentFormState>(
    index: number,
    field: Field,
    value: ExperimentFormState[Field],
  ) => {
    setExperiments((previous) =>
      previous.map((experiment, experimentIndex) =>
        experimentIndex === index
          ? {
              ...experiment,
              [field]: value,
            }
          : experiment,
      ),
    )
  }

  const handleNameChange = (index: number, value: string) => {
    updateExperiment(index, 'name', value)
  }

  const handleEngineChange = (index: number, value: string) => {
    updateExperiment(index, 'engine', value)
  }

  const handleControllerChange = (index: number, value: string) => {
    updateExperiment(index, 'controller', value)
  }

  const handleEpisodesChange = (index: number, value: string) => {
    const trimmed = value.trim()
    const parsed = trimmed === '' ? undefined : Number(trimmed)
    updateExperiment(
      index,
      'episodes',
      Number.isNaN(parsed) ? undefined : parsed,
    )
  }

  const handleReportingToggle = (index: number, enabled: boolean) => {
    setExperiments((previous) =>
      previous.map((experiment, experimentIndex) =>
        experimentIndex === index
          ? {
              ...experiment,
              reportingEnabled: enabled,
              reporting: enabled
                ? experiment.reporting
                : {
                    plots: false,
                    denormalizeState: false,
                    export: false,
                  },
            }
          : experiment,
      ),
    )
  }

  const handleReportingOptionChange = (
    index: number,
    option: keyof ExperimentFormState['reporting'],
    value: boolean,
  ) => {
    setExperiments((previous) =>
      previous.map((experiment, experimentIndex) =>
        experimentIndex === index
          ? {
              ...experiment,
              reporting: {
                ...experiment.reporting,
                [option]: value,
              },
            }
          : experiment,
      ),
    )
  }

  const handleAddExperiment = () => {
    setExperiments((previous) => [...previous, createDefaultExperiment()])
  }

  const handleRemoveExperiment = (index: number) => {
    setExperiments((previous) =>
      previous.length <= 1
        ? previous
        : previous.filter((_, experimentIndex) => experimentIndex !== index),
    )
  }

  const handleToggleDevMode = () => {
    if (!devMode) {
      setEditorValue(buildExperimentYaml(experiments))
      setDevMode(true)
      return
    }

    try {
      const parsed = parseExperimentYaml(editorValue)
      if (parsed.length === 0) {
        setExperiments([createDefaultExperiment()])
      } else {
        setExperiments(parsed)
      }
      setDevMode(false)
    } catch (error) {
      console.error('Invalid YAML, keeping previous state', error)
      toast.error(
        'Invalid YAML. Please fix the syntax before leaving Dev Mode.',
      )
    }
  }

  const handleSave = () => {
    if (devMode) {
      try {
        const parsed = parseExperimentYaml(editorValue)
        setExperiments(parsed.length > 0 ? parsed : [createDefaultExperiment()])
      } catch (error) {
        console.error(
          'Invalid YAML. Could not save experiment configuration',
          error,
        )
        toast.error('Invalid YAML. Could not save experiment configuration.')
        return
      }
    }

    setSaveDialogOpen(true)
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      const text = await file.text()
      const parsed = parseExperimentYaml(text)
      const normalized =
        parsed.length > 0 ? parsed : [createDefaultExperiment()]
      setExperiments(normalized)
      setOpenedFile(file.name)
      if (devMode) {
        setEditorValue(buildExperimentYaml(normalized))
      }
      toast.success(`Imported experiment configuration from ${file.name}`)
    } catch (error) {
      console.error('Failed to parse uploaded experiment YAML file', error)
      toast.error('Failed to parse uploaded experiment configuration.')
    } finally {
      event.target.value = ''
    }
  }

  const handleOpenConfig = () => {
    setConfigDialogOpen(true)
  }

  const handleSelectConfig = async (name: string) => {
    try {
      const { content } = await fetchExperimentConfig(name)
      const yamlStr = JSON.stringify(content, null, 2)
      const parsed = parseExperimentYaml(yamlStr)
      const normalized =
        parsed.length > 0 ? parsed : [createDefaultExperiment()]
      setExperiments(normalized)
      if (devMode) {
        setEditorValue(buildExperimentYaml(normalized))
      }
      setOpenedFile(name)
      toast.success(`Loaded experiment configuration ${name}`)
    } catch (error) {
      console.error('Failed to load experiment config', error)
      toast.error('Failed to load experiment configuration')
    }
  }

  const handleEnvironmentSelect = (name: string) => {
    if (environmentDialogIndex === null) return

    updateExperiment(environmentDialogIndex, 'environmentConfig', name)
    setEnvironmentDialogIndex(null)
  }

  const handleControllerSelect = (name: string) => {
    if (controllerDialogIndex === null) return

    updateExperiment(controllerDialogIndex, 'controllerConfig', name)
    setControllerDialogIndex(null)
  }

  return (
    <>
      <ExperimentToolbar
        devMode={devMode}
        onToggleDevMode={handleToggleDevMode}
        onSave={handleSave}
        onUpload={handleUploadClick}
        onOpenConfig={handleOpenConfig}
        fileInputRef={fileInputRef}
        onFileChange={handleFileChange}
      >
        {openedFile && (
          <Badge variant="default" className="w-fit">
            {openedFile}
          </Badge>
        )}
        {devMode ? (
          <CustomEditor
            defaultLanguage="yaml"
            value={resolvedYaml}
            onChange={(value) => setEditorValue(value ?? '')}
            height="600px"
          />
        ) : (
          <div className="flex flex-col gap-6">
            {experiments.map((experiment, index) => (
              <Card key={`experiment-${index}`}>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-lg font-semibold">
                    Experiment {index + 1}
                  </CardTitle>
                  <Button
                    type="button"
                    size="icon"
                    onClick={() => handleRemoveExperiment(index)}
                    disabled={experiments.length <= 1}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="flex flex-col gap-1">
                      <label className="text-primary text-sm font-semibold">
                        Name
                      </label>
                      <Input
                        value={experiment.name}
                        onChange={(event) =>
                          handleNameChange(index, event.target.value)
                        }
                        placeholder="My Experiment"
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-primary text-sm font-semibold">
                        Engine
                      </label>
                      <Input
                        value={experiment.engine}
                        onChange={(event) =>
                          handleEngineChange(index, event.target.value)
                        }
                        placeholder="sinergym"
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-primary text-sm font-semibold">
                        Environment Config
                      </label>
                      <div className="flex w-full flex-col gap-2 md:flex-row">
                        <Input
                          value={experiment.environmentConfig}
                          onChange={(event) =>
                            updateExperiment(
                              index,
                              'environmentConfig',
                              event.target.value,
                            )
                          }
                        />
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => setEnvironmentDialogIndex(index)}
                          className="w-full"
                        >
                          Choose Environment Config
                        </Button>
                      </div>
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-primary text-sm font-semibold">
                        Controller
                      </label>
                      <Select
                        value={experiment.controller}
                        onValueChange={(value) =>
                          handleControllerChange(index, value)
                        }
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select controller" />
                        </SelectTrigger>
                        <SelectContent>
                          {controllerOptions.map((option) => {
                            return (
                              <SelectItem key={option.key} value={option.key}>
                                {option.name}
                              </SelectItem>
                            )
                          })}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-primary text-sm font-semibold">
                        Controller Config
                      </label>
                      <div className="flex w-full flex-col gap-2 md:flex-row">
                        <Input
                          value={experiment.controllerConfig}
                          onChange={(event) =>
                            updateExperiment(
                              index,
                              'controllerConfig',
                              event.target.value,
                            )
                          }
                        />
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => setControllerDialogIndex(index)}
                          className="w-full"
                        >
                          Choose Controller Config
                        </Button>
                      </div>
                    </div>
                    <div className="flex flex-col gap-1">
                      <label
                        className="text-primary text-sm font-semibold"
                        htmlFor={`episodes-${index}`}
                      >
                        Episodes
                      </label>
                      <Input
                        id={`episodes-${index}`}
                        type="number"
                        min={1}
                        value={experiment.episodes ?? ''}
                        onChange={(event) =>
                          handleEpisodesChange(index, event.target.value)
                        }
                        placeholder="1"
                      />
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    <label className="text-primary flex items-center gap-2 text-sm font-semibold">
                      <Checkbox
                        checked={experiment.reportingEnabled}
                        onCheckedChange={(checked) =>
                          handleReportingToggle(index, !!checked)
                        }
                      />
                      Reporting
                    </label>

                    {experiment.reportingEnabled && (
                      <div className="ml-6 flex flex-col gap-2 text-sm">
                        <label className="flex items-center gap-2">
                          <Checkbox
                            checked={experiment.reporting.plots}
                            onCheckedChange={(checked) =>
                              handleReportingOptionChange(
                                index,
                                'plots',
                                !!checked,
                              )
                            }
                          />
                          Plots
                        </label>
                        <label className="flex items-center gap-2">
                          <Checkbox
                            checked={experiment.reporting.denormalizeState}
                            onCheckedChange={(checked) =>
                              handleReportingOptionChange(
                                index,
                                'denormalizeState',
                                !!checked,
                              )
                            }
                          />
                          Denormalize state
                        </label>
                        <label className="flex items-center gap-2">
                          <Checkbox
                            checked={experiment.reporting.export}
                            onCheckedChange={(checked) =>
                              handleReportingOptionChange(
                                index,
                                'export',
                                !!checked,
                              )
                            }
                          />
                          Export
                        </label>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}

            <div>
              <Button type="button" onClick={handleAddExperiment}>
                <Plus className="mr-2 h-4 w-4" /> Add Experiment
              </Button>
            </div>
          </div>
        )}
      </ExperimentToolbar>

      <ExperimentSaveDialog
        open={saveDialogOpen}
        onClose={() => setSaveDialogOpen(false)}
        experiments={experiments}
        onSaved={(filename) => {
          setOpenedFile(filename)
        }}
        initialFilename={openedFile}
      />

      <ExperimentConfigDialog
        open={configDialogOpen}
        onClose={() => setConfigDialogOpen(false)}
        onSelect={handleSelectConfig}
      />

      <EnvironmentConfigDialog
        open={environmentDialogIndex !== null}
        onClose={() => setEnvironmentDialogIndex(null)}
        onSelect={handleEnvironmentSelect}
      />

      <ControllerConfigDialog
        open={controllerDialogIndex !== null}
        onClose={() => setControllerDialogIndex(null)}
        onSelect={handleControllerSelect}
      />
    </>
  )
}

export default ExperimentConfigurator
