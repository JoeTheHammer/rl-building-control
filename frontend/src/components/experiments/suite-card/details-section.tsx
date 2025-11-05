import React from 'react'

import { Button } from '@/components/ui/button.tsx'
import { CardContent } from '@/components/ui/card.tsx'
import type {
  ExperimentConfigDetailsResponse,
  ExperimentRunStatusResponse,
  ExperimentSuiteStatus,
} from '@/services/experiment-service.ts'

import LogViewer from './log-viewer.tsx'
import ProgressSection from './progress-section.tsx'
import type { ActiveConfigState } from './hooks/use-config-dialog.ts'

interface DetailsSectionProps {
  status: ExperimentSuiteStatus
  configName?: string
  configDetails: ExperimentConfigDetailsResponse | null
  progressById: Map<number, ExperimentRunStatusResponse['experiments'][number]>
  statusLoading: boolean
  statusError: string | null
  hasStatusEntries: boolean
  openConfigDialog: (config: Exclude<ActiveConfigState, null>) => void
  suiteId?: number
  onShowCompletedLogs: (open: boolean) => void
  logLines: string[]
  logLoading: boolean
  logError: string | null
  dataFolderPath?: string
  experimentConfigFile?: string
}

const DetailsSection: React.FC<DetailsSectionProps> = ({
  status,
  configName,
  configDetails,
  progressById,
  statusLoading,
  statusError,
  hasStatusEntries,
  openConfigDialog,
  suiteId,
  onShowCompletedLogs,
  logLines,
  logLoading,
  logError,
  dataFolderPath,
  experimentConfigFile,
}) => {
  const experimentDetails = configDetails?.experiments ?? []

  return (
    <CardContent className="bg-muted/20 border-primary/10 space-y-4 border-t pt-4">
      <div className="flex flex-wrap items-center gap-2">
        <Button
          onClick={() => openConfigDialog({ type: 'experiment' })}
          disabled={!configDetails?.experiment}
        >
          Show Experiment Config
        </Button>
        {(status === 'Finished' || status === 'Aborted') && (
          <Button
            onClick={() => onShowCompletedLogs(true)}
            disabled={typeof suiteId !== 'number'}
          >
            Show logs
          </Button>
        )}
      </div>

      {experimentConfigFile && (
        <span className="text-xs">
          <strong>Experiment:</strong> {experimentConfigFile}
        </span>
      )}

      <div className="space-y-4">
        {experimentDetails.length > 0 ? (
          experimentDetails.map((experiment, index) => {
            const progress = progressById.get(experiment.id)
            const showLoading =
              status === 'Running' &&
              statusLoading &&
              !hasStatusEntries &&
              !progress
            const showError =
              status === 'Running' && index === 0 ? statusError : null
            const environmentPath = experiment.environment_path?.trim()
            const controllerPath = experiment.controller_path?.trim()
            const hasPathInfo = Boolean(
              environmentPath ||
                controllerPath ||
                dataFolderPath ||
                experimentConfigFile,
            )

            return (
              <div
                key={experiment.id}
                className="border-border/40 bg-background/60 space-y-3 rounded-md border p-4"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-semibold md:text-base">
                    Name: {experiment.name ?? `Experiment ${experiment.id}`}
                  </span>
                  <Button
                    onClick={() =>
                      openConfigDialog({
                        type: 'environment',
                        experimentId: experiment.id,
                      })
                    }
                    disabled={!experiment.environment}
                  >
                    Show Environment Config
                  </Button>
                  <Button
                    onClick={() =>
                      openConfigDialog({
                        type: 'controller',
                        experimentId: experiment.id,
                      })
                    }
                    disabled={!experiment.controller}
                  >
                    Show Controller Config
                  </Button>
                </div>
                {hasPathInfo && (
                  <div className="text-muted-foreground flex flex-col space-y-1 text-xs">
                    {dataFolderPath && (
                      <span>
                        <strong>Data folder:</strong> {dataFolderPath + '/'}
                      </span>
                    )}

                    {environmentPath && (
                      <span>
                        <strong>Environment:</strong> {environmentPath}
                      </span>
                    )}
                    {controllerPath && (
                      <span>
                        <strong>Controller:</strong> {controllerPath}
                      </span>
                    )}
                  </div>
                )}
                {status === 'Running' && (
                  <ProgressSection
                    progress={progress ?? null}
                    loading={showLoading}
                    error={showError}
                  />
                )}
              </div>
            )
          })
        ) : (
          <p className="text-muted-foreground text-sm">
            No experiments were found in this configuration.
          </p>
        )}
      </div>

      {status === 'Running' && (
        <LogViewer
          title="Logs"
          lines={logLines}
          loading={logLoading}
          error={logError}
        />
      )}
    </CardContent>
  )
}

export default DetailsSection
