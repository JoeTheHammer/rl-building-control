import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Info } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { AxiosError } from 'axios'

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
  createExperimentLogEventSource,
  fetchExperimentConfigDetails,
  fetchExperimentSuiteLogs,
  fetchExperimentSuiteStatus,
} from '@/services/experiment-service.ts'
import type { LocalExperimentSuite } from '@/components/experiments/types.ts'

import ConfigSectionDialog from './config-details-dialog.tsx'
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
    if (isProgressLine(line) && next.length > 0 && isProgressLine(next[next.length - 1])) {
      next[next.length - 1] = line
    } else {
      next.push(line)
    }
  }
  return next
}

type Suite = LocalExperimentSuite | ExperimentSuiteApiResponse

interface SuiteCardProps {
  suite: Suite
  status: ExperimentSuiteStatus
  idLabel?: string
  actions: React.ReactNode
}

const SuiteCard: React.FC<SuiteCardProps> = ({ suite, status, idLabel, actions }) => {
  const navigate = useNavigate()
  const isLocal = 'localId' in suite
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [activeConfigSection, setActiveConfigSection] = useState<
    'experiment' | 'environment' | 'controller' | null
  >(null)
  const [configDetails, setConfigDetails] =
    useState<ExperimentConfigDetailsResponse | null>(null)
  const [configLoading, setConfigLoading] = useState(false)
  const [configError, setConfigError] = useState<string | null>(null)
  const [statusInfo, setStatusInfo] = useState<ExperimentRunStatusResponse | null>(null)
  const [statusLoading, setStatusLoading] = useState(false)
  const [statusError, setStatusError] = useState<string | null>(null)
  const [logLines, setLogLines] = useState<string[]>([])
  const [logLoading, setLogLoading] = useState(false)
  const [logError, setLogError] = useState<string | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  const configName = useMemo(() => {
    if (isLocal) return suite.configName
    return suite.config_filename ?? undefined
  }, [isLocal, suite])

  const suiteId = !isLocal ? suite.id : undefined

  const fileName = useMemo(() => {
    if (isLocal) {
      return getFileName(suite.configName)
    }
    const persisted = suite as ExperimentSuiteApiResponse
    return getFileName(persisted.config_filename ?? persisted.name)
  }, [isLocal, suite])

  const fullPath = useMemo(() => {
    if (isLocal) return undefined
    return (suite as ExperimentSuiteApiResponse).path ?? undefined
  }, [isLocal, suite])

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

  const shouldLoadStatus = detailsOpen && status === 'Running' && typeof suiteId === 'number'

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

  const handleEdit = (section: 'experiment' | 'environment' | 'controller') => {
    if (!configDetails) {
      setActiveConfigSection(null)
      return
    }

    if (section === 'experiment' && configDetails.experiment) {
      navigate('/experiment-configurator', {
        state: { initialExperimentConfig: configDetails.experiment },
      })
    } else if (section === 'environment' && configDetails.environment) {
      navigate('/environment-configurator', {
        state: { initialEnvironmentConfig: configDetails.environment },
      })
    } else if (section === 'controller' && configDetails.controller) {
      navigate('/controller-configurator', {
        state: { initialControllerConfig: configDetails.controller },
      })
    }
    setActiveConfigSection(null)
  }

  const handleDialogOpenChange = (open: boolean) => {
    if (!open) {
      setActiveConfigSection(null)
    }
  }

  const openSectionDialog = (
    section: 'experiment' | 'environment' | 'controller',
  ) => {
    if (!configName) {
      setConfigError('No configuration file associated with this suite')
      setActiveConfigSection(null)
      return
    }
    setConfigError(null)
    setActiveConfigSection(section)
  }

  const activeSection = (() => {
    if (!activeConfigSection || !configDetails) {
      return null
    }
    if (activeConfigSection === 'experiment') {
      return configDetails.experiment
    }
    if (activeConfigSection === 'environment') {
      return configDetails.environment ?? null
    }
    return configDetails.controller ?? null
  })()

  const dialogTitle =
    activeConfigSection !== null
      ? `${
          activeConfigSection.charAt(0).toUpperCase() +
          activeConfigSection.slice(1)
        }`
      : ''

  return (
    <Collapsible open={detailsOpen} onOpenChange={setDetailsOpen} className="w-full">
      <Card className="border-primary/20">
        <CardContent className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-3">
              <CardTitle className="text-primary text-lg">{suite.name}</CardTitle>
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
            <CollapsibleTrigger asChild>
              <Button variant="outline" className="gap-2">
                <Info className="size-4" />
                {detailsOpen ? 'Hide details' : 'Show details'}
              </Button>
            </CollapsibleTrigger>
            {actions}
          </div>
        </CardContent>

        <CollapsibleContent>
          <CardContent className="bg-muted/20 border-t border-primary/10 space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="outline"
                onClick={() => openSectionDialog('experiment')}
                disabled={!configName}
              >
                Show experiment config
              </Button>
              <Button
                variant="outline"
                onClick={() => openSectionDialog('environment')}
                disabled={!configName}
              >
                Show environment config
              </Button>
              <Button
                variant="outline"
                onClick={() => openSectionDialog('controller')}
                disabled={!configName}
              >
                Show controller config
              </Button>
            </div>

            {status === 'Running' && (
              <div className="space-y-4">
                <ProgressSection
                  status={statusInfo}
                  loading={statusLoading}
                  error={statusError}
                />
                <LogViewer
                  title="Logs (optional)"
                  lines={logLines}
                  loading={logLoading}
                  error={logError}
                />
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Card>

      <ConfigSectionDialog
        open={activeConfigSection !== null}
        onOpenChange={handleDialogOpenChange}
        title={dialogTitle}
        section={activeSection}
        loading={configLoading}
        error={configError}
        onEdit={
          activeConfigSection
            ? () => handleEdit(activeConfigSection)
            : undefined
        }
      />
    </Collapsible>
  )
}

export default SuiteCard
