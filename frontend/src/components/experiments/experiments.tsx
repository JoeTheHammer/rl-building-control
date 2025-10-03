import React, { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Archive,
  CalendarPlus,
  ChartNoAxesCombined,
  Play,
  Square,
  Trash2,
} from 'lucide-react'
import { toast } from 'sonner'

import CustomPage from '@/components/shared/page.tsx'
import ExperimentConfigDialog from '@/components/configurator/experiment/experiment-config-dialog.tsx'
import { Button } from '@/components/ui/button.tsx'
import {
  archiveExperimentSuite,
  fetchExperimentConfig,
  fetchExperimentSuites,
  runExperimentSuite,
  stopExperimentSuite,
  type ExperimentSuiteApiResponse,
  type TensorBoardStatusResponse,
} from '@/services/experiment-service.ts'
import SuiteCard from '@/components/experiments/suite-card/suite-card.tsx'
import type { LocalExperimentSuite } from '@/components/experiments/types.ts'

const createLocalId = (): string =>
  typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2)

const Experiments = () => {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [localSuites, setLocalSuites] = useState<LocalExperimentSuite[]>([])
  const [persistedSuites, setPersistedSuites] = useState<
    ExperimentSuiteApiResponse[]
  >([])
  const [pendingRuns, setPendingRuns] = useState<string[]>([])
  const [pendingStops, setPendingStops] = useState<number[]>([])
  const [pendingArchives, setPendingArchives] = useState<number[]>([])

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
    if (!persistedSuites.some((s) => s.status === 'Running')) return
    const interval = window.setInterval(refreshPersistedSuites, 5000)
    return () => window.clearInterval(interval)
  }, [persistedSuites, refreshPersistedSuites])

  const runningSuites = useMemo(
    () => persistedSuites.filter((s) => s.status === 'Running'),
    [persistedSuites],
  )
  const completedSuites = useMemo(
    () =>
      persistedSuites.filter(
        (suite) => suite.status !== 'Running' && !suite.archived,
      ),
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
          : configName

      setLocalSuites((prev) => [
        { localId: createLocalId(), name: derivedName, configName },
        ...prev,
      ])
    } catch (error) {
      console.error('Failed to schedule experiment suite', error)
      toast.error('Unable to schedule experiment suite')
    }
  }, [])

  const handleRunSuite = useCallback(
    async (localId: string) => {
      const suite = localSuites.find((s) => s.localId === localId)
      if (!suite) return
      setPendingRuns((p) => [...p, localId])

      try {
        const response = await runExperimentSuite({
          configName: suite.configName,
          suiteName: suite.name,
        })
        setLocalSuites((p) => p.filter((s) => s.localId !== localId))
        setPersistedSuites((prev) => [response, ...prev])
        toast.success(`Started "${suite.name}"`)
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
      } catch (error) {
        toast.error('Unable to start experiment suite')
      } finally {
        setPendingRuns((p) => p.filter((id) => id !== localId))
        await refreshPersistedSuites()
      }
    },
    [localSuites, refreshPersistedSuites],
  )

  const handleTensorboardStatusChange = useCallback(
    (suiteId: number, status: TensorBoardStatusResponse) => {
      setPersistedSuites((prev) =>
        prev.map((suite) =>
          suite.id === suiteId
            ? {
                ...suite,
                tensorboard: status,
                tensorboard_enabled: status.enabled,
              }
            : suite,
        ),
      )
    },
    [],
  )

  const handleDeleteSuite = (localId: string) =>
    setLocalSuites((p) => p.filter((s) => s.localId !== localId))

  const handleStopSuite = useCallback(
    async (suiteId: number) => {
      setPendingStops((p) => [...p, suiteId])
      try {
        const response = await stopExperimentSuite(suiteId)
        setPersistedSuites((prev) =>
          prev.map((s) =>
            s.id === suiteId ? { ...s, status: response.status, pid: null } : s,
          ),
        )
        toast.success('Experiment suite aborted')
      } catch {
        toast.error('Unable to stop experiment suite')
      } finally {
        setPendingStops((p) => p.filter((id) => id !== suiteId))
        await refreshPersistedSuites()
      }
    },
    [refreshPersistedSuites],
  )

  const handleArchiveSuite = useCallback(
    async (suiteId: number) => {
      setPendingArchives((p) => [...p, suiteId])
      try {
        const response = await archiveExperimentSuite(suiteId)
        setPersistedSuites((prev) =>
          prev.map((suite) => (suite.id === suiteId ? response : suite)),
        )
        toast.success(`Archived "${response.name}"`)
      } catch {
        toast.error('Unable to archive experiment suite')
      } finally {
        setPendingArchives((p) => p.filter((id) => id !== suiteId))
        await refreshPersistedSuites()
      }
    },
    [refreshPersistedSuites],
  )

  return (
    <CustomPage>
      <div className="flex flex-col gap-6 pt-4">
        <div className="flex items-center justify-between">
          <span className="text-primary text-xl font-bold">
            Experiment Suites
          </span>
          <Button onClick={() => setDialogOpen(true)} className="gap-2">
            <CalendarPlus className="size-4" /> Schedule Experiment Suite
          </Button>
        </div>

        {/* New */}
        <Section title="New Experiment Suites">
          {localSuites.length === 0 ? (
            <EmptyState message="No experiment suites scheduled yet." />
          ) : (
            localSuites.map((suite) => (
              <SuiteCard
                key={suite.localId}
                suite={suite}
                status="New"
                actions={
                  <div className="flex gap-2">
                    <Button
                      onClick={() => handleRunSuite(suite.localId)}
                      disabled={pendingRuns.includes(suite.localId)}
                      className="gap-2"
                    >
                      <Play className="size-4" /> Run
                    </Button>
                    <Button
                      onClick={() => handleDeleteSuite(suite.localId)}
                      className="gap-2"
                    >
                      <Trash2 className="size-4" /> Remove
                    </Button>
                  </div>
                }
              />
            ))
          )}
        </Section>

        {/* Running */}
        <Section title="Running Experiment Suites">
          {runningSuites.length === 0 ? (
            <EmptyState message="There are no running experiment suites." />
          ) : (
            runningSuites.map((suite) => (
              <SuiteCard
                key={suite.id}
                suite={suite}
                status={suite.status}
                idLabel={`ID: ${suite.id}`}
                actions={
                  <Button
                    onClick={() => handleStopSuite(suite.id)}
                    disabled={pendingStops.includes(suite.id)}
                  >
                    <div className="flex gap-2">
                      <Square className="size-4" /> Stop
                    </div>
                  </Button>
                }
                onTensorboardStatusChange={(status) =>
                  handleTensorboardStatusChange(suite.id, status)
                }
              />
            ))
          )}
        </Section>

        {/* Completed */}
        <Section title="Completed Experiment Suites">
          {completedSuites.length === 0 ? (
            <EmptyState message="No experiment suites have finished yet." />
          ) : (
            completedSuites.map((suite) => (
              <SuiteCard
                key={suite.id}
                suite={suite}
                status={suite.status}
                idLabel={`ID: ${suite.id}`}
                actions={
                  <div className="flex gap-2">
                    {!suite.archived && (
                      <Button
                        onClick={() => handleArchiveSuite(suite.id)}
                        disabled={pendingArchives.includes(suite.id)}
                        className="gap-2"
                      >
                        <Archive className="size-4" /> Archive
                      </Button>
                    )}
                    <Button
                      onClick={() => console.log('Handle show results')}
                      disabled={pendingStops.includes(suite.id)}
                    >
                      <div className="flex gap-2">
                        <ChartNoAxesCombined className="size-4" /> Show Results
                      </div>
                    </Button>
                  </div>
                }
                onTensorboardStatusChange={(status) =>
                  handleTensorboardStatusChange(suite.id, status)
                }
              />
            ))
          )}
        </Section>
      </div>

      <ExperimentConfigDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSelect={handleScheduleSuite}
      />
    </CustomPage>
  )
}

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({
  title,
  children,
}) => (
  <div className="border-primary/20 bg-background rounded-xl border p-6 shadow-sm">
    <h2 className="text-primary mb-4 text-xl font-semibold">{title}</h2>
    <div className="space-y-4">{children}</div>
  </div>
)

const EmptyState: React.FC<{ message: string }> = ({ message }) => (
  <div className="border-primary/30 text-muted-foreground rounded-lg border border-dashed px-4 py-6 text-center">
    {message}
  </div>
)

export default Experiments
