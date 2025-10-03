import React, { useEffect, useMemo, useRef, useState } from 'react'
import { BarChart3, ChevronDown, ChevronUp, Power } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { AxiosError } from 'axios'
import { toast } from 'sonner'

import { Badge } from '@/components/ui/badge.tsx'
import { Button } from '@/components/ui/button.tsx'
import {
  Card,
  CardContent,
  CardDescription,
  CardTitle,
} from '@/components/ui/card.tsx'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible.tsx'
import { cn } from '@/lib/utils.ts'
import type {
  ExperimentConfigDetailsResponse,
  ExperimentRunStatusResponse,
  ExperimentSuiteApiResponse,
  ExperimentSuiteStatus,
} from '@/services/experiment-service.ts'
import {
  EXPERIMENT_API_BASE,
  createExperimentLogEventSource,
  fetchExperimentConfigDetails,
  fetchExperimentSuiteLogs,
  fetchExperimentSuiteStatus,
  startTensorBoard,
  stopTensorBoard,
  type TensorBoardStatusResponse,
  type StopTensorBoardResponse,
} from '@/services/experiment-service.ts'
import type { LocalExperimentSuite } from '@/components/experiments/types.ts'

import ConfigSectionDialog from './config-details-dialog.tsx'
import CompletedLogDialog from './completed-log-dialog.tsx'
import ProgressSection from './progress-section.tsx'
import LogViewer from './log-viewer.tsx'

const getStatusBadgeClass = (status: ExperimentSuiteStatus): string => {
  switch (status) {
    case 'Running':
      return 'bg-emerald-500 text-white'
    case 'Finished':
      return 'bg-green-800 text-primary-foreground'
    case 'Aborted':
      return 'bg-red-800 text-primary-foreground'
    default:
      return 'bg-secondary text-secondary-foreground'
  }
}

const getFileName = (path?: string): string =>
  path ? (path.split('/').pop() ?? path) : 'Unknown'

const splitLines = (content: string): string[] => {
  const normalized = content.replace(/\r\n/g, '\n')
  const lines = normalized.split('\n')
  if (lines.length && lines[lines.length - 1] === '') {
    lines.pop()
  }
  return lines
}

const isProgressLine = (line: string): boolean =>
  line.trim().toLowerCase().startsWith('simulation progress')

const mergeLogLines = (current: string[], incoming: string[]): string[] => {
  if (incoming.length === 0) return current
  const next = [...current]
  for (const line of incoming) {
    if (line === '' && next.length === 0) {
      continue
    }
    if (
      isProgressLine(line) &&
      next.length > 0 &&
      isProgressLine(next[next.length - 1])
    ) {
      next[next.length - 1] = line
    } else {
      next.push(line)
    }
  }
  return next
}

type Suite = LocalExperimentSuite | ExperimentSuiteApiResponse

type ActiveConfigState =
  | { type: 'experiment' }
  | { type: 'environment'; experimentId: number }
  | { type: 'controller'; experimentId: number }
  | null

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
  const navigate = useNavigate()
  const isLocal = 'localId' in suite
  const persistedSuite = isLocal ? null : (suite as ExperimentSuiteApiResponse)
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [activeConfig, setActiveConfig] = useState<ActiveConfigState>(null)
  const [configDetails, setConfigDetails] =
    useState<ExperimentConfigDetailsResponse | null>(null)
  const [configLoading, setConfigLoading] = useState(false)
  const [configError, setConfigError] = useState<string | null>(null)
  const [statusInfo, setStatusInfo] =
    useState<ExperimentRunStatusResponse | null>(null)
  const [statusLoading, setStatusLoading] = useState(false)
  const [statusError, setStatusError] = useState<string | null>(null)
  const [logLines, setLogLines] = useState<string[]>([])
  const [logLoading, setLogLoading] = useState(false)
  const [logError, setLogError] = useState<string | null>(null)
  const [completedLogsOpen, setCompletedLogsOpen] = useState(false)
  const [completedLogLines, setCompletedLogLines] = useState<string[]>([])
  const [completedLogsLoading, setCompletedLogsLoading] = useState(false)
  const [completedLogsError, setCompletedLogsError] = useState<string | null>(
    null,
  )
  const [tensorboardStatus, setTensorboardStatus] =
    useState<TensorBoardStatusResponse | null>(null)
  const [tensorboardLoading, setTensorboardLoading] = useState(false)
  const [tensorboardStopping, setTensorboardStopping] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)

  const configName = useMemo(() => {
    if (isLocal) return (suite as LocalExperimentSuite).configName
    return persistedSuite?.config_filename ?? undefined
  }, [isLocal, persistedSuite, suite])

  const suiteId = persistedSuite?.id

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

  const tensorboardEnabled = persistedSuite?.tensorboard_enabled ?? false
  const canAccessTensorboard =
    tensorboardEnabled || tensorboardStatus?.enabled === true

  const fileName = useMemo(() => {
    if (isLocal) {
      return getFileName((suite as LocalExperimentSuite).configName)
    }
    if (!persistedSuite) return 'Unknown'
    return getFileName(persistedSuite.config_filename ?? persistedSuite.name)
  }, [isLocal, persistedSuite, suite])

  const fullPath = useMemo(() => {
    if (isLocal) return undefined
    return persistedSuite?.path ?? undefined
  }, [isLocal, persistedSuite])

  useEffect(() => {
    setTensorboardStatus(initialTensorboardStatus)
  }, [initialTensorboardStatus])

  const experimentDetails = configDetails?.experiments ?? []

  const progressById = useMemo(() => {
    const map = new Map<
      number,
      ExperimentRunStatusResponse['experiments'][number]
    >()
    const experiments = statusInfo?.experiments ?? []
    for (const entry of experiments) {
      map.set(entry.id, entry)
    }
    return map
  }, [statusInfo])

  const hasStatusEntries = (statusInfo?.experiments?.length ?? 0) > 0

  useEffect(() => {
    if (!detailsOpen || !configName) {
      return
    }
    let ignore = false
    setConfigLoading(true)
    setConfigError(null)
    fetchExperimentConfigDetails(configName)
      .then((data) => {
        if (ignore) return
        setConfigDetails(data)
      })
      .catch((error: unknown) => {
        if (ignore) return
        const responseStatus = (error as AxiosError)?.response?.status
        if (responseStatus === 404) {
          setConfigDetails(null)
          setConfigError('Configuration file could not be found')
        } else {
          console.error('Failed to load configuration details', error)
          setConfigError('Unable to load configuration details')
        }
      })
      .finally(() => {
        if (!ignore) {
          setConfigLoading(false)
        }
      })

    return () => {
      ignore = true
    }
  }, [configName, detailsOpen])

  useEffect(() => {
    if (
      typeof window === 'undefined' ||
      typeof navigator === 'undefined' ||
      typeof suiteId !== 'number' ||
      !tensorboardStatus?.running
    ) {
      return
    }

    const endpoint = `${EXPERIMENT_API_BASE}/suites/${suiteId}/tensorboard/stop`

    const handleBeforeUnload = () => {
      try {
        const payload = JSON.stringify({ reason: 'window-unload' })
        const blob = new Blob([payload], { type: 'application/json' })
        navigator.sendBeacon(endpoint, blob)
      } catch (error) {
        console.debug('TensorBoard shutdown beacon failed', error)
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [suiteId, tensorboardStatus?.running])

  const shouldLoadStatus =
    detailsOpen && status === 'Running' && typeof suiteId === 'number'

  useEffect(() => {
    if (!shouldLoadStatus || typeof suiteId !== 'number') {
      setStatusInfo(null)
      setStatusError(null)
      setStatusLoading(false)
      return
    }

    let ignore = false
    let firstFetch = true

    const fetchStatus = async () => {
      if (firstFetch) {
        setStatusLoading(true)
      }
      try {
        const data = await fetchExperimentSuiteStatus(suiteId)
        if (ignore) return
        setStatusInfo(data)
        setStatusError(null)
      } catch (error: unknown) {
        if (ignore) return
        const responseStatus = (error as AxiosError)?.response?.status
        if (responseStatus === 404) {
          setStatusInfo(null)
          setStatusError(null)
        } else {
          console.error('Failed to load status file', error)
          setStatusError('Unable to read progress information')
        }
      } finally {
        if (!ignore) {
          setStatusLoading(false)
        }
        firstFetch = false
      }
    }

    fetchStatus()
    const interval = window.setInterval(fetchStatus, 2000)

    return () => {
      ignore = true
      window.clearInterval(interval)
    }
  }, [shouldLoadStatus, suiteId])

  const shouldStreamLogs = shouldLoadStatus

  useEffect(() => {
    if (!shouldStreamLogs || typeof suiteId !== 'number') {
      setLogLines([])
      setLogError(null)
      setLogLoading(false)
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
      return
    }

    let ignore = false
    setLogLoading(true)
    setLogError(null)

    fetchExperimentSuiteLogs(suiteId)
      .then(({ content }) => {
        if (ignore) return
        setLogLines(mergeLogLines([], splitLines(content)))
      })
      .catch((error: unknown) => {
        if (ignore) return
        const responseStatus = (error as AxiosError)?.response?.status
        if (responseStatus === 404) {
          setLogLines([])
        } else {
          console.error('Failed to load logs', error)
          setLogError('Unable to load logs')
        }
      })
      .finally(() => {
        if (!ignore) {
          setLogLoading(false)
        }
      })

    if (typeof window !== 'undefined' && 'EventSource' in window) {
      const source = createExperimentLogEventSource(suiteId)
      eventSourceRef.current = source
      source.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as { lines?: string[] }
          if (Array.isArray(payload.lines)) {
            setLogLines((prev) => mergeLogLines(prev, payload.lines ?? []))
          }
        } catch (error) {
          console.error('Failed to parse log stream payload', error)
        }
      }
      source.onerror = () => {
        setLogError((prev) => prev ?? 'Log stream disconnected')
        source.close()
        if (eventSourceRef.current === source) {
          eventSourceRef.current = null
        }
      }
    }

    return () => {
      ignore = true
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [shouldStreamLogs, suiteId])

  const updateTensorboardStatus = (status: TensorBoardStatusResponse) => {
    setTensorboardStatus(status)
    onTensorboardStatusChange?.(status)
  }

  const handleOpenTensorboard = async () => {
    if (typeof suiteId !== 'number') {
      return
    }
    if (!canAccessTensorboard) {
      toast.error('TensorBoard is not enabled for this suite')
      return
    }

    setTensorboardLoading(true)
    try {
      const wasRunning = tensorboardStatus?.running === true
      const status = await startTensorBoard(suiteId, 'ui')

      updateTensorboardStatus(status)

      if (!status.enabled) {
        toast.error('TensorBoard is disabled for this suite')
        return
      }

      if (!wasRunning) {
        toast.success('TensorBoard started')
      }

      if (status.url) {
        window.open(status.url, '_blank', 'noopener,noreferrer')
      } else {
        toast.info('TensorBoard is starting, please try again in a few seconds')
      }
    } catch (error) {
      console.error('Failed to open TensorBoard', error)
      toast.error('Unable to open TensorBoard')
    } finally {
      setTensorboardLoading(false)
    }
  }

  const handleStopTensorboard = async () => {
    if (typeof suiteId !== 'number') {
      return
    }

    setTensorboardStopping(true)
    try {
      const response: StopTensorBoardResponse = await stopTensorBoard(
        suiteId,
        'user-request',
      )
      updateTensorboardStatus(response)

      if (response.stopped) {
        toast.success('TensorBoard stopped')
      } else {
        toast.info('TensorBoard was not running')
      }
    } catch (error) {
      console.error('Failed to stop TensorBoard', error)
      toast.error('Unable to stop TensorBoard')
    } finally {
      setTensorboardStopping(false)
    }
  }

  const handleEdit = () => {
    if (!activeConfig || !configDetails) {
      setActiveConfig(null)
      return
    }

    if (activeConfig.type === 'experiment' && configDetails.experiment) {
      navigate('/experiment-configurator', {
        state: { initialExperimentConfig: configDetails.experiment },
      })
    } else if (activeConfig.type === 'environment') {
      const entry = configDetails.experiments?.find(
        (item) => item.id === activeConfig.experimentId,
      )
      if (entry?.environment) {
        navigate('/environment-configurator', {
          state: { initialEnvironmentConfig: entry.environment },
        })
      }
    } else if (activeConfig.type === 'controller') {
      const entry = configDetails.experiments?.find(
        (item) => item.id === activeConfig.experimentId,
      )
      if (entry?.controller) {
        navigate('/controller-configurator', {
          state: { initialControllerConfig: entry.controller },
        })
      }
    }
    setActiveConfig(null)
  }

  const handleDialogOpenChange = (open: boolean) => {
    if (!open) {
      setActiveConfig(null)
    }
  }

  const openConfigDialog = (config: Exclude<ActiveConfigState, null>) => {
    if (!configName) {
      setConfigError('No configuration file associated with this suite')
      setActiveConfig(null)
      return
    }
    setConfigError(null)
    setActiveConfig(config)
  }

  useEffect(() => {
    if (!completedLogsOpen) {
      return
    }

    if (typeof suiteId !== 'number') {
      setCompletedLogLines([])
      setCompletedLogsError(
        'Logs are only available for saved experiment suites',
      )
      setCompletedLogsLoading(false)
      return
    }

    let ignore = false
    setCompletedLogsLoading(true)
    setCompletedLogsError(null)

    fetchExperimentSuiteLogs(suiteId)
      .then(({ content }) => {
        if (ignore) return
        setCompletedLogLines(splitLines(content))
      })
      .catch((error: unknown) => {
        if (ignore) return
        const responseStatus = (error as AxiosError)?.response?.status
        if (responseStatus === 404) {
          setCompletedLogLines([])
          setCompletedLogsError('Log file could not be found for this suite')
        } else {
          console.error('Failed to load completed logs', error)
          setCompletedLogsError('Unable to load logs for this suite')
        }
      })
      .finally(() => {
        if (!ignore) {
          setCompletedLogsLoading(false)
        }
      })

    return () => {
      ignore = true
    }
  }, [completedLogsOpen, suiteId])

  const handleCompletedLogsOpenChange = (open: boolean) => {
    setCompletedLogsOpen(open)
    if (!open) {
      setCompletedLogsError(null)
    }
  }

  const activeSection = useMemo(() => {
    if (!activeConfig || !configDetails) {
      return null
    }
    if (activeConfig.type === 'experiment') {
      return configDetails.experiment ?? null
    }
    const entry = configDetails.experiments?.find(
      (item) => item.id === activeConfig.experimentId,
    )
    if (!entry) {
      return null
    }
    if (activeConfig.type === 'environment') {
      return entry.environment ?? null
    }
    return entry.controller ?? null
  }, [activeConfig, configDetails])

  const dialogTitle = useMemo(() => {
    if (!activeConfig) {
      return ''
    }
    const base =
      activeConfig.type === 'experiment'
        ? 'Experiment'
        : activeConfig.type === 'environment'
          ? 'Environment'
          : 'Controller'
    if (activeConfig.type === 'experiment') {
      return base
    }
    const entry = configDetails?.experiments?.find(
      (item) => item.id === activeConfig.experimentId,
    )
    const name = entry?.name ?? `Experiment ${activeConfig.experimentId}`
    return `${base} – ${name}`
  }, [activeConfig, configDetails])

  return (
    <Collapsible
      open={detailsOpen}
      onOpenChange={setDetailsOpen}
      className="w-full"
    >
      <Card className="border-primary/20">
        <CardContent className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-3">
              <CardTitle className="text-primary text-lg">
                {suite.name}
              </CardTitle>
              <Badge
                className={cn(
                  'px-3 py-1 text-xs font-semibold uppercase',
                  getStatusBadgeClass(status),
                )}
              >
                {String(status)}
              </Badge>
            </div>

            <CardDescription className="text-muted-foreground text-sm font-medium">
              File: {fileName}
            </CardDescription>

            {fullPath && (
              <CardDescription className="text-muted-foreground text-xs">
                Path: {fullPath}
              </CardDescription>
            )}

            {idLabel && (
              <CardDescription className="text-muted-foreground text-sm font-medium">
                {idLabel}
              </CardDescription>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {persistedSuite ? (
              <Button
                onClick={handleOpenTensorboard}
                disabled={tensorboardLoading || !canAccessTensorboard}
                className="gap-2"
              >
                <BarChart3 className="size-4" /> Open TensorBoard
              </Button>
            ) : null}
            {persistedSuite && tensorboardStatus?.running ? (
              <Button
                onClick={handleStopTensorboard}
                disabled={tensorboardStopping}
                className="gap-2"
              >
                <Power className="size-4" /> Stop TensorBoard
              </Button>
            ) : null}
            <CollapsibleTrigger asChild>
              <Button variant="outline" className="gap-2">
                {detailsOpen ? (
                  <ChevronUp className="size-4" />
                ) : (
                  <ChevronDown className="size-4" />
                )}
                {detailsOpen ? 'Hide details' : 'Show details'}
              </Button>
            </CollapsibleTrigger>
            {actions}
          </div>
        </CardContent>

        <CollapsibleContent>
          <CardContent className="bg-muted/20 border-primary/10 space-y-4 border-t pt-4">
            <div className="flex flex-wrap items-center gap-2">
              <Button
                onClick={() => openConfigDialog({ type: 'experiment' })}
                disabled={!configName}
              >
                Show experiment config
              </Button>
              {(status === 'Finished' || status === 'Aborted') && (
                <Button
                  onClick={() => handleCompletedLogsOpenChange(true)}
                  disabled={typeof suiteId !== 'number'}
                >
                  Show logs
                </Button>
              )}
            </div>

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
                  const hasPathInfo = Boolean(environmentPath || controllerPath)

                  return (
                    <div
                      key={experiment.id}
                      className="border-border/40 bg-background/60 space-y-3 rounded-md border p-4"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-semibold md:text-base">
                          Name:{' '}
                          {experiment.name ?? `Experiment ${experiment.id}`}
                        </span>
                        <Button
                          onClick={() =>
                            openConfigDialog({
                              type: 'environment',
                              experimentId: experiment.id,
                            })
                          }
                          disabled={!configName || !experiment.environment}
                        >
                          Show environment config
                        </Button>
                        <Button
                          onClick={() =>
                            openConfigDialog({
                              type: 'controller',
                              experimentId: experiment.id,
                            })
                          }
                          disabled={!configName || !experiment.controller}
                        >
                          Show controller config
                        </Button>
                      </div>
                      {hasPathInfo && (
                        <div className="text-muted-foreground text-xs sm:flex sm:flex-wrap sm:items-center sm:gap-6">
                          {environmentPath && (
                            <span className="block">
                              Environment: {environmentPath}
                            </span>
                          )}
                          {controllerPath && (
                            <span className="block">
                              Controller: {controllerPath}
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
