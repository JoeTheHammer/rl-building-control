import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs.tsx'
import EnvGeneralTab from './env-general-tab.tsx'
import EnvStateSpaceTab from './env-state-space-tab.tsx'
import EnvActionSpaceTab from './env-action-space-tab.tsx'
import EnvRewardTab from './env-reward-tab.tsx'
import CustomPage from '../../shared/page.tsx'

const tabTriggerStyle =
  'text-md text-foreground hover:text-primary-foreground hover:bg-primary-hover hover:cursor-pointer active:bg-primary ' +
  'data-[state=active]:bg-primary data-[state=active]:text-primary-foreground shadow-md'

const EnvironmentConfigurator = () => {
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
            <EnvGeneralTab />
          </TabsContent>
          <TabsContent value="stateSpace">
            <EnvStateSpaceTab />
          </TabsContent>
          <TabsContent value="actionSpace">
            <EnvActionSpaceTab />
          </TabsContent>
          <TabsContent value="reward">
            <EnvRewardTab />
          </TabsContent>
        </Tabs>
      </div>
    </CustomPage>
  )
}

export default EnvironmentConfigurator
