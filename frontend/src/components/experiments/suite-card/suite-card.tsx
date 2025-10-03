import React, { useMemo, useState } from 'react'

import { Card, CardContent } from '@/components/ui/card.tsx'
import { Collapsible, CollapsibleContent } from '@/components/ui/collapsible.tsx'
import type {
  ExperimentSuiteApiResponse,
  ExperimentSuiteStatus,
  TensorBoardStatusResponse,
} from '@/services/experiment-service.ts'

import CompletedLogDialog from './completed-log-dialog.tsx'
import ConfigSectionDialog from './config-details-dialog.tsx'
import DetailsSection from './details-section.tsx'
import HeaderSection from './header-section.tsx'
import { useConfigDialog } from './hooks/use-config-dialog.ts'
import { useCompletedLogs } from './hooks/use-completed-logs.ts'
import { useSuiteConfig } from './hooks/use-suite-config.ts'
import { useSuiteLogs } from './hooks/use-suite-logs.ts'
import { useSuiteStatus } from './hooks/use-suite-status.ts'
import { useTensorboardControls } from './hooks/use-tensorboard-controls.ts'
import type { Suite, TensorboardControls } from './types.ts'
import { getFileName } from './utils.ts'

interface SuiteCardProps {
  suite: Suite
  status: ExperimentSuiteStatus
  idLabel?: string
  actions: React.ReactNode
  onTensorboardStatusChange?: (status: TensorBoardStatusResponse) => void
}

const SuiteCard: React.FC<SuiteCardProps> = ({
  suite,
  status,
  idLabel,
  actions,
  onTensorboardStatusChange,
}) => {
  const [detailsOpen, setDetailsOpen] = useState(false)

  const isLocal = 'localId' in suite
  const persistedSuite = (isLocal ? null : suite) as ExperimentSuiteApiResponse | null
  const suiteId = persistedSuite?.id

  const configName = useMemo(() => {
    if (isLocal) return suite.configName
    return persistedSuite?.config_filename ?? undefined
  }, [isLocal, persistedSuite, suite])

  const fileName = useMemo(() => {
    if (isLocal) {
      return getFileName(suite.configName)
    }
    if (!persistedSuite) return 'Unknown'
    return getFileName(persistedSuite.config_filename ?? persistedSuite.name)
  }, [isLocal, persistedSuite, suite])

  const fullPath = useMemo(() => {
    if (isLocal) return undefined
    return persistedSuite?.path ?? undefined
  }, [isLocal, persistedSuite])

  const initialTensorboardStatus = useMemo(() => {
    if (!persistedSuite) {
      return null
    }
    const info = persistedSuite.tensorboard ?? {
      enabled: persistedSuite.tensorboard_enabled ?? false,
      running: false,
    }
    return {
      suite_id: persistedSuite.id,
      enabled: info.enabled ?? false,
      running: info.running ?? false,
      url: info.url ?? null,
      port: info.port ?? null,
      pid: info.pid ?? null,
      owner: info.owner ?? null,
      started_at: info.started_at ?? null,
      expires_at: info.expires_at ?? null,
    }
  }, [persistedSuite])

  const {
    configDetails,
    configLoading,
    configError,
    setConfigError,
  } = useSuiteConfig({ configName, detailsOpen })

  const {
    shouldLoadStatus,
    statusLoading,
    statusError,
    progressById,
    hasStatusEntries,
  } = useSuiteStatus({ suiteId, detailsOpen, status })

  const { logLines, logLoading, logError } = useSuiteLogs({
    suiteId,
    shouldStream: shouldLoadStatus,
  })

  const {
    tensorboardStatus,
    canAccessTensorboard,
    openTensorboard,
    stopTensorboard,
    tensorboardLoading,
    tensorboardStopping,
  } = useTensorboardControls({
    suiteId,
    initialStatus: initialTensorboardStatus,
    tensorboardEnabled: persistedSuite?.tensorboard_enabled ?? false,
    onTensorboardStatusChange,
  })

  const {
    completedLogsOpen,
    completedLogLines,
    completedLogsLoading,
    completedLogsError,
    handleCompletedLogsOpenChange,
  } = useCompletedLogs({ suiteId })

  const {
    activeConfig,
    openConfigDialog,
    handleDialogOpenChange,
    handleEdit,
    activeSection,
    dialogTitle,
  } = useConfigDialog({
    configDetails,
    configName,
    setConfigError,
  })

  const tensorboardControls: TensorboardControls | null = persistedSuite
    ? {
        onOpen: (event) => {
          event.preventDefault()
          void openTensorboard()
        },
        onStop: (event) => {
          event.preventDefault()
          void stopTensorboard()
        },
        disabled: tensorboardLoading || !canAccessTensorboard,
        isLoading: tensorboardLoading,
        isRunning: tensorboardStatus?.running ?? false,
        isStopping: tensorboardStopping,
      }
    : null

  return (
    <Collapsible open={detailsOpen} onOpenChange={setDetailsOpen} className="w-full">
      <Card className="border-primary/20">
        <CardContent className="flex flex-col gap-4">
          <HeaderSection
            suite={suite}
            status={status}
            fileName={fileName}
            fullPath={fullPath}
            idLabel={idLabel}
            actions={actions}
            detailsOpen={detailsOpen}
            tensorboard={tensorboardControls}
          />
        </CardContent>

        <CollapsibleContent>
          <DetailsSection
            status={status}
            configName={configName}
            configDetails={configDetails}
            progressById={progressById}
            statusLoading={statusLoading}
            statusError={statusError}
            hasStatusEntries={hasStatusEntries}
            openConfigDialog={openConfigDialog}
            suiteId={suiteId}
            onShowCompletedLogs={handleCompletedLogsOpenChange}
            logLines={logLines}
            logLoading={logLoading}
            logError={logError}
          />
        </CollapsibleContent>
      </Card>

      <ConfigSectionDialog
        open={activeConfig !== null}
        onOpenChange={handleDialogOpenChange}
        title={dialogTitle}
        section={activeSection}
        loading={configLoading}
        error={configError}
        onEdit={activeConfig ? handleEdit : undefined}
      />
      <CompletedLogDialog
        open={completedLogsOpen}
        onOpenChange={handleCompletedLogsOpenChange}
        lines={completedLogLines}
        loading={completedLogsLoading}
        error={completedLogsError}
      />
    </Collapsible>
  )
}

export default SuiteCard
