import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { CalendarPlus, Info, Play, Square } from 'lucide-react'
import { toast } from 'sonner'

import CustomPage from '@/components/shared/page.tsx'
import ExperimentConfigDialog from '@/components/configurator/experiment/experiment-config-dialog.tsx'
import { Badge } from '@/components/ui/badge.tsx'
import { Button } from '@/components/ui/button.tsx'
import {
  Card,
  CardContent,
  CardDescription,
  CardTitle,
} from '@/components/ui/card.tsx'
import { cn } from '@/lib/utils.ts'
import {
  fetchExperimentConfig,
  fetchExperimentSuites,
  runExperimentSuite,
  stopExperimentSuite,
  stripExperimentExtension,
  type ExperimentSuiteApiResponse,
  type ExperimentSuiteStatus,
} from '@/services/experiment-service.ts'

interface LocalExperimentSuite {
  localId: string
  name: string
  configName: string
}

const createLocalId = (): string => {
  if (
    typeof crypto !== 'undefined' &&
    typeof crypto.randomUUID === 'function'
  ) {
    return crypto.randomUUID()
  }

  return Math.random().toString(36).slice(2)
}

const prettifyName = (value: string): string =>
  stripExperimentExtension(value)
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())

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

const Experiments = () => {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [localSuites, setLocalSuites] = useState<LocalExperimentSuite[]>([])
  const [persistedSuites, setPersistedSuites] = useState<
    ExperimentSuiteApiResponse[]
  >([])
  const [pendingRuns, setPendingRuns] = useState<string[]>([])
  const [pendingStops, setPendingStops] = useState<number[]>([])

  const refreshPersistedSuites = useCallback(async () => {
    try {
      const suites = await fetchExperimentSuites()
      setPersistedSuites(suites)
    } catch (error) {
      console.error('Failed to load experiment suites', error)
    }
  }, [])

  useEffect(() => {
    refreshPersistedSuites()
  }, [refreshPersistedSuites])

  useEffect(() => {
    if (!persistedSuites.some((suite) => suite.status === 'Running')) {
      return
    }

    const interval = window.setInterval(() => {
      refreshPersistedSuites()
    }, 5000)

    return () => window.clearInterval(interval)
  }, [persistedSuites, refreshPersistedSuites])

  const runningSuites = useMemo(
    () => persistedSuites.filter((suite) => suite.status === 'Running'),
    [persistedSuites],
  )

  const completedSuites = useMemo(
    () => persistedSuites.filter((suite) => suite.status !== 'Running'),
    [persistedSuites],
  )

  const handleScheduleSuite = useCallback(async (configName: string) => {
    try {
      const config = await fetchExperimentConfig(configName)
      const content = config.content as {
        experiments?: Array<{ name?: string }>
      }
      const experiments = Array.isArray(content?.experiments)
        ? content.experiments
        : []

      const derivedName =
        experiments.length === 1 && experiments[0]?.name
          ? experiments[0].name
          : prettifyName(configName)

      const newSuite: LocalExperimentSuite = {
        localId: createLocalId(),
        name: derivedName ?? prettifyName(configName),
        configName,
      }

      setLocalSuites((previous) => [newSuite, ...previous])
      toast.success(`Scheduled "${newSuite.name}"`)
    } catch (error) {
      console.error('Failed to schedule experiment suite', error)
      toast.error('Unable to schedule experiment suite')
    }
  }, [])

  const handleRunSuite = useCallback(
    async (localId: string) => {
      const suite = localSuites.find((item) => item.localId === localId)
      if (!suite) {
        return
      }

      setPendingRuns((previous) => [...previous, localId])

      try {
        const response = await runExperimentSuite({
          configName: suite.configName,
          suiteName: suite.name,
        })

        setLocalSuites((previous) =>
          previous.filter((item) => item.localId !== localId),
        )
        setPersistedSuites((previous) => {
          const filtered = previous.filter((item) => item.id !== response.id)
          return [response, ...filtered]
        })

        toast.success(`Started "${suite.name}"`)
      } catch (error) {
        console.error('Failed to start experiment suite', error)
        toast.error('Unable to start experiment suite')
      } finally {
        setPendingRuns((previous) => previous.filter((id) => id !== localId))
        await refreshPersistedSuites()
      }
    },
    [localSuites, refreshPersistedSuites],
  )

  const handleStopSuite = useCallback(
    async (suiteId: number) => {
      setPendingStops((previous) => [...previous, suiteId])

      try {
        const response = await stopExperimentSuite(suiteId)
        setPersistedSuites((previous) =>
          previous.map((suite) =>
            suite.id === suiteId
              ? { ...suite, status: response.status, pid: null }
              : suite,
          ),
        )
        toast.success('Experiment suite aborted')
      } catch (error) {
        console.error('Failed to stop experiment suite', error)
        toast.error('Unable to stop experiment suite')
      } finally {
        setPendingStops((previous) => previous.filter((id) => id !== suiteId))
        await refreshPersistedSuites()
      }
    },
    [refreshPersistedSuites],
  )

  const renderSuiteCard = (
    suite: LocalExperimentSuite | ExperimentSuiteApiResponse,
    status: ExperimentSuiteStatus,
    actions: React.ReactNode,
    idLabel?: string,
  ) => {
    return (
      <Card
        key={'localId' in suite ? suite.localId : suite.id}
        className="border-primary/20"
      >
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
            {idLabel && (
              <CardDescription className="text-muted-foreground text-sm font-medium">
                {idLabel}
              </CardDescription>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="outline" disabled className="gap-2">
              <Info className="size-4" />
              Show details
            </Button>
            {actions}
          </div>
        </CardContent>
      </Card>
    )
  }
  return (
    <CustomPage>
      <div className="flex flex-col gap-2 pt-2">
        <div className="flex items-center justify-between">
          <span className="text-primary text-md pt-2 font-bold md:text-xl">
            Experiment Suites
          </span>

          <Button
            onClick={() => setDialogOpen(true)}
            className="gap-2"
            type="button"
          >
            <CalendarPlus className="size-4" />
            Schedule Experiment Suite
          </Button>
        </div>

        <hr className="border-t-primary w-full pb-2" />

        <div className="flex flex-col gap-6">
          <div className="border-primary/20 bg-background rounded-xl border p-6 shadow-sm">
            <div className="mb-4 flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-primary text-xl font-semibold">
                  New Experiment Suites
                </h2>
              </div>
            </div>
            <div className="space-y-4">
              {localSuites.length === 0 && (
                <div className="border-primary/30 text-muted-foreground rounded-lg border border-dashed px-4 py-6 text-center">
                  No experiment suites scheduled yet.
                </div>
              )}
              {localSuites.map((suite) => {
                const isPending = pendingRuns.includes(suite.localId)
                return renderSuiteCard(
                  suite,
                  'New',
                  <Button
                    key={`run-${suite.localId}`}
                    className="gap-2"
                    onClick={() => handleRunSuite(suite.localId)}
                    disabled={isPending}
                    type="button"
                  >
                    <Play className="size-4" />
                    Run
                  </Button>,
                )
              })}
            </div>
          </div>

          <div className="border-primary/20 bg-background rounded-xl border p-6 shadow-sm">
            <div className="mb-4 flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-primary text-xl font-semibold">
                  Running Experiment Suites
                </h2>
              </div>
            </div>
            <div className="space-y-4">
              {runningSuites.length === 0 && (
                <div className="border-primary/30 text-muted-foreground rounded-lg border border-dashed px-4 py-6 text-center">
                  There are no running experiment suites.
                </div>
              )}
              {runningSuites.map((suite) => {
                const isPending = pendingStops.includes(suite.id)
                return renderSuiteCard(
                  suite,
                  suite.status,
                  <Button
                    key={`stop-${suite.id}`}
                    onClick={() => handleStopSuite(suite.id)}
                    disabled={isPending}
                    type="button"
                  >
                    <div className="flex flex-row gap-2">
                      <Square className="size-4" />
                      Stop
                    </div>
                  </Button>,
                  `ID: ${suite.id}`,
                )
              })}
            </div>
          </div>

          <div className="border-primary/20 bg-background rounded-xl border p-6 shadow-sm">
            <div className="mb-4 flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-primary text-xl font-semibold">
                  Completed Experiment Suites
                </h2>
              </div>
            </div>
            <div className="space-y-4">
              {completedSuites.length === 0 && (
                <div className="border-primary/30 text-muted-foreground rounded-lg border border-dashed px-4 py-6 text-center">
                  No experiment suites have finished yet.
                </div>
              )}
              {completedSuites.map((suite) =>
                renderSuiteCard(
                  suite,
                  suite.status,
                  <Button
                    key={`details-${suite.id}`}
                    variant="outline"
                    disabled
                    className="gap-2"
                  >
                    <Info className="size-4" />
                    Show details
                  </Button>,
                  `ID: ${suite.id}`,
                ),
              )}
            </div>
          </div>
        </div>
      </div>

      <ExperimentConfigDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSelect={handleScheduleSuite}
      />
    </CustomPage>
  )
}

export default Experiments
