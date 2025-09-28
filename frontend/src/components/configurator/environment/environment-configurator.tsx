import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs.tsx'
import EnvStateSpaceTab, {
  type EnvironmentStateSpaceSettings,
} from './env-state-space-tab.tsx'
import EnvActionSpaceTab, {
  type EnvActionSpaceSettings,
} from './env-action-space-tab.tsx'
import EnvRewardTab, {
  type EnvironmentRewardSettings,
} from './env-reward-tab.tsx'
import CustomPage from '../../shared/page.tsx'
import React, { useMemo, useRef, useState } from 'react'
import EnvGeneralTab, {
  type EnvironmentGeneralSettings,
} from './env-general-tab.tsx'
import { Button } from '../../ui/button.tsx'
import { Save, Code2, Monitor, Import, FolderOpen } from 'lucide-react'
import {
  buildEnvironmentYaml,
  parseEnvironmentYaml,
} from '@/services/yaml-service.ts'
import CustomEditor from '../../shared/custom-editor.tsx'
import EnvironmentConfigDialog from '@/components/configurator/environment/environment-config-dialog.tsx'
import EnvironmentSaveDialog from '@/components/configurator/environment/environment-save-dialog.tsx'
import { fetchEnvironmentConfig } from '@/services/environment-service.ts'
import { Badge } from '@/components/ui/badge.tsx'
import { toast } from 'sonner'

const tabTriggerStyle =
  'text-md text-primary hover:text-primary-foreground hover:bg-primary/90 hover:cursor-pointer active:bg-primary ' +
  'data-[state=active]:bg-primary data-[state=active]:text-primary-foreground shadow-md'

const EnvironmentConfigurator = () => {
  const [generalSettings, setGeneralSettings] =
    useState<EnvironmentGeneralSettings>({
      buildingModelFile: null,
      weatherDataFile: null,
      startDate: '',
      endDate: '',
      timestepsPerHour: undefined,
    })

  const [stateSpaceSettings, setStateSpaceSettings] =
    useState<EnvironmentStateSpaceSettings>({
      addTimeInfo: false,
      dayOfMonth: { included: false, cyclic: false },
      dayOfWeek: { included: false, cyclic: false },
      hour: { included: false, cyclic: false },
      minute: { included: false, cyclic: false },
      month: { included: false, cyclic: false },
      variables: [
        {
          name: '',
          variableType: 'variable',
          energyPlusType: '',
          zone: '',
        },
      ],
    })

  const [actionSpaceSettings, setActionSpaceSettings] =
    useState<EnvActionSpaceSettings>({
      actuators: [
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
      ],
    })

  const [rewardSettings, setRewardSettings] =
    useState<EnvironmentRewardSettings>({
      type: 'expression',
      variables: [],
      parameters: [],
      expression: '',
      moduleName: '',
      className: '',
      codeParameters: [],
    })

  // Dev mode
  const [devMode, setDevMode] = useState(false)
  const [editorValue, setEditorValue] = useState('')
  const [openedFile, setOpenedFile] = useState<string | null>(null)

  // Dialog state
  const [configDialogOpen, setConfigDialogOpen] = useState(false)
  const [saveDialogOpen, setSaveDialogOpen] = useState(false)

  const handleGeneralSettingsChange = (
    changes: Partial<EnvironmentGeneralSettings>,
  ) => setGeneralSettings((prev) => ({ ...prev, ...changes }))

  const handleStateSpaceSettingsChange = (
    changes: Partial<EnvironmentStateSpaceSettings>,
  ) => setStateSpaceSettings((prev) => ({ ...prev, ...changes }))

  const handleActionSpaceSettingsChange = (
    changes: Partial<EnvActionSpaceSettings>,
  ) => setActionSpaceSettings((prev) => ({ ...prev, ...changes }))

  const handleRewardSettingsChange = (
    changes: Partial<EnvironmentRewardSettings>,
  ) => setRewardSettings((prev) => ({ ...prev, ...changes }))

  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const text = await file.text()
      const parsed = parseEnvironmentYaml(text)
      setGeneralSettings(parsed.generalSettings)
      setStateSpaceSettings(parsed.stateSpaceSettings)
      setActionSpaceSettings(parsed.actionSpaceSettings)
      setRewardSettings(parsed.rewardSettings)
      console.log('Uploaded and parsed environment YAML', parsed)
    } catch (error) {
      console.error('Failed to parse uploaded YAML file', error)
    } finally {
      e.target.value = ''
      setOpenedFile(null)
    }
  }

  const handleSave = () => {
    if (devMode) {
      try {
        const parsed = parseEnvironmentYaml(editorValue)
        setGeneralSettings(parsed.generalSettings)
        setStateSpaceSettings(parsed.stateSpaceSettings)
        setActionSpaceSettings(parsed.actionSpaceSettings)
        setRewardSettings(parsed.rewardSettings)
        console.log('Saved from Dev Mode', parsed)
      } catch (err) {
        console.error('Invalid YAML. Could not save.', err)
        toast.error('Invalid YAML. Could not save environment configuration.')
        return
      }
    }

    setSaveDialogOpen(true)
  }

  const handleToggleDevMode = () => {
    if (!devMode) {
      const yamlString = buildEnvironmentYaml(
        generalSettings,
        stateSpaceSettings,
        actionSpaceSettings,
        rewardSettings,
      )
      setEditorValue(yamlString)
      setDevMode(true)
    } else {
      try {
        const parsed = parseEnvironmentYaml(editorValue)
        setGeneralSettings(parsed.generalSettings)
        setStateSpaceSettings(parsed.stateSpaceSettings)
        setActionSpaceSettings(parsed.actionSpaceSettings)
        setRewardSettings(parsed.rewardSettings)
        console.log('Dev Mode exited, state updated from YAML')
      } catch (err) {
        console.error('Invalid YAML, keeping previous state', err)
      }
      setDevMode(false)
    }
  }

  const handleOpenConfiguration = async (name: string) => {
    try {
      const { content } = await fetchEnvironmentConfig(name)
      const yamlStr = JSON.stringify(content, null, 2)
      const parsed = parseEnvironmentYaml(yamlStr)

      setGeneralSettings(parsed.generalSettings)
      setStateSpaceSettings(parsed.stateSpaceSettings)
      setActionSpaceSettings(parsed.actionSpaceSettings)
      setRewardSettings(parsed.rewardSettings)

      setOpenedFile(name)

      if (devMode) {
        setEditorValue(
          buildEnvironmentYaml(
            parsed.generalSettings,
            parsed.stateSpaceSettings,
            parsed.actionSpaceSettings,
            parsed.rewardSettings,
          ),
        )
      }

      console.log('Loaded environment config:', name, parsed)
    } catch (err) {
      console.error('Failed to load environment config', err)
    }
  }

  const currentConfig = useMemo(
    () => ({
      generalSettings,
      stateSpaceSettings,
      actionSpaceSettings,
      rewardSettings,
    }),
    [
      generalSettings,
      stateSpaceSettings,
      actionSpaceSettings,
      rewardSettings,
    ],
  )

  return (
    <CustomPage>
      <div className="flex w-full flex-col gap-2 pt-2">
        {/* Grid for buttons */}
        <div className="mb-2 grid grid-cols-5 items-center gap-2">
          <div className="col-span-2 col-start-1">
            <span className="text-primary text-md pt-2 font-bold md:text-xl">
              Environment Configurator
            </span>
          </div>
          <div className="col-start-3 w-full">
            <Button
              onClick={handleToggleDevMode}
              type="button"
              variant={devMode ? 'default' : 'ghost'}
              className="text-md flex w-full gap-2 border"
            >
              {devMode ? (
                <>
                  <Monitor />
                  Switch to GUI Mode
                </>
              ) : (
                <>
                  <Code2 />
                  Switch to Dev Mode
                </>
              )}
            </Button>
          </div>

          <div className="col-start-4 w-full">
            <Button
              onClick={() => setConfigDialogOpen(true)}
              type="button"
              className="text-md w-full"
            >
              <div className="flex gap-2">
                <FolderOpen />
                <span>Open Configuration</span>
              </div>
            </Button>
            <EnvironmentConfigDialog
              open={configDialogOpen}
              onClose={() => setConfigDialogOpen(false)}
              onSelect={handleOpenConfiguration}
            />
          </div>

          <div className="md:col-start-5">
            <Button
              onClick={handleUploadClick}
              type="button"
              className="text-md w-full"
            >
              <div className="flex items-center gap-2">
                <Import />
                <span>Import Configuration</span>
              </div>
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".yaml,.yml"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>

          <div className="col-start-6 w-full">
            <Button
              onClick={handleSave}
              type="button"
              className="text-md p- w-full cursor-pointer"
            >
              <div className="flex gap-2">
                <Save />
                <span>Save Configuration</span>
              </div>
            </Button>
            <EnvironmentSaveDialog
              open={saveDialogOpen}
              onClose={() => setSaveDialogOpen(false)}
              initialFilename={openedFile}
              config={currentConfig}
              onSaved={(filename) => {
                setOpenedFile(filename)
              }}
            />
          </div>
        </div>

        <hr className="border-t-primary w-full pb-2" />

        {openedFile !== null && openedFile !== '' && (
          <Badge variant="default">
            <span>{openedFile}</span>
          </Badge>
        )}

        {devMode ? (
          <CustomEditor
            defaultLanguage="yaml"
            value={editorValue}
            onChange={(val) => setEditorValue(val ?? '')}
            height="600px"
          />
        ) : (
          <Tabs defaultValue="general">
            <TabsList className="w-full gap-4">
              <TabsTrigger value="general" className={tabTriggerStyle}>
                General
              </TabsTrigger>
              <TabsTrigger value="stateSpace" className={tabTriggerStyle}>
                State Space
              </TabsTrigger>
              <TabsTrigger value="actionSpace" className={tabTriggerStyle}>
                Action Space
              </TabsTrigger>
              <TabsTrigger value="reward" className={tabTriggerStyle}>
                Reward
              </TabsTrigger>
            </TabsList>
            <TabsContent value="general">
              <EnvGeneralTab
                settings={generalSettings}
                onSettingsChange={handleGeneralSettingsChange}
              />
            </TabsContent>
            <TabsContent value="stateSpace">
              <EnvStateSpaceTab
                settings={stateSpaceSettings}
                onSettingsChange={handleStateSpaceSettingsChange}
              />
            </TabsContent>
            <TabsContent value="actionSpace">
              <EnvActionSpaceTab
                settings={actionSpaceSettings}
                onSettingsChange={handleActionSpaceSettingsChange}
              />
            </TabsContent>
            <TabsContent value="reward">
              <EnvRewardTab
                settings={rewardSettings}
                onSettingsChange={handleRewardSettingsChange}
              />
            </TabsContent>
          </Tabs>
        )}
      </div>
    </CustomPage>
  )
}

export default EnvironmentConfigurator
