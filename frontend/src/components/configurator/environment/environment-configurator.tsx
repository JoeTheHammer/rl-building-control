import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs.tsx'
import EnvStateSpaceTab, {
  type EnvironmentStateSpaceSettings,
} from './env-state-space-tab.tsx'
import EnvActionSpaceTab from './env-action-space-tab.tsx'
import EnvRewardTab from './env-reward-tab.tsx'
import CustomPage from '../../shared/page.tsx'
import { useState } from 'react'
import EnvGeneralTab, {
  type EnvironmentGeneralSettings,
} from './env-general-tab.tsx'
import { Button } from '../../ui/button.tsx'
import { Save } from 'lucide-react'

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
      variables: [],
    })

  const handleGeneralSettingsChange = (
    changes: Partial<EnvironmentGeneralSettings>,
  ) => {
    setGeneralSettings((prev) => ({ ...prev, ...changes }))
  }

  const handleStateSpaceSettingsChange = (
    changes: Partial<EnvironmentStateSpaceSettings>,
  ) => {
    setStateSpaceSettings((prev) => ({ ...prev, ...changes }))
  }

  const handleSave = () => {
    console.log('Saving environment configuration', {
      generalSettings,
      stateSpaceSettings,
    })
  }

  return (
    <CustomPage headline={'Environment Configurator'}>
      <div className="flex w-full flex-col gap-2 pt-2">
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
            <EnvActionSpaceTab />
          </TabsContent>
          <TabsContent value="reward">
            <EnvRewardTab />
          </TabsContent>
        </Tabs>
        <div className="mt-8 flex justify-end">
          <Button
            onClick={handleSave}
            type="button"
            className="text-md cursor-pointer"
          >
            <div className="flex gap-2">
              <Save />
              <span>Save</span>
            </div>
          </Button>
        </div>
      </div>
    </CustomPage>
  )
}

export default EnvironmentConfigurator
