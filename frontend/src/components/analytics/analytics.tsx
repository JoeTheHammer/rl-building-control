import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { FileDown, Loader2, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { useLocation, useSearchParams } from 'react-router-dom'

import CustomPage from '@/components/shared/page.tsx'
import { Button } from '@/components/ui/button.tsx'
import DatasetViewer from '@/components/analytics/dataset-viewer.tsx'
import LoadDataDialog from '@/components/analytics/load-data-dialog.tsx'
import CsvExportDialog, {
  type CsvOption,
} from '@/components/analytics/csv-export-dialog.tsx'
import type {
  AnalyticsDataResponse,
  AnalyticsExperiment,
  AnalyticsSuiteSummary,
} from '@/services/analytics-service.ts'
import {
  downloadAnalyticsSuiteFile,
  fetchAnalyticsSuiteData,
  fetchAnalyticsSuites,
} from '@/services/analytics-service.ts'

interface ExportSeriesDefinition {
  option: CsvOption
  values: number[]
}

const escapeCsvValue = (value: string | number | undefined): string => {
  if (value === undefined || value === null) return ''
  const stringValue = String(value)
  return /[",\n]/.test(stringValue)
    ? `"${stringValue.replace(/"/g, '""')}"`
    : stringValue
}

const parseSuiteId = (value: unknown): number | null => {
  if (value === null || value === undefined) {
    return null
  }

  if (typeof value === 'number' && Number.isFinite(value)) {
    return Math.trunc(value)
  }

  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number.parseInt(value, 10)
    if (!Number.isNaN(parsed)) {
      return parsed
    }
  }

  return null
}

const Analytics: React.FC = () => {
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  const [loadDialogOpen, setLoadDialogOpen] = useState(false)
  const [csvDialogOpen, setCsvDialogOpen] = useState(false)
  const [suites, setSuites] = useState<AnalyticsSuiteSummary[]>([])
  const [suitesLoading, setSuitesLoading] = useState(false)
  const [selectedSuite, setSelectedSuite] =
    useState<AnalyticsSuiteSummary | null>(null)
  const [suiteData, setSuiteData] = useState<AnalyticsDataResponse | null>(null)
  const [loadingData, setLoadingData] = useState(false)
  const [selectedCsvOptions, setSelectedCsvOptions] = useState<string[]>([])
  const [autoLoadSuiteId, setAutoLoadSuiteId] = useState<number | null>(null)
  const requestedSuiteIdRef = useRef<number | null>(null)

  const requestedSuiteId = useMemo(() => {
    const state = location.state as { suiteId?: unknown } | null
    const stateSuiteId = parseSuiteId(state?.suiteId)
    if (stateSuiteId !== null) {
      return stateSuiteId
    }

    return parseSuiteId(searchParams.get('suiteId'))
  }, [location.state, searchParams])

  const loadSuites = useCallback(async () => {
    setSuitesLoading(true)
    try {
      const response = await fetchAnalyticsSuites()
      setSuites(response)
    } catch (error) {
      console.error('Failed to fetch analytics suites', error)
      toast.error('Unable to load experiment suites')
    } finally {
      setSuitesLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSuites()
  }, [loadSuites])

  useEffect(() => {
    if (requestedSuiteId === null) {
      requestedSuiteIdRef.current = null
      setAutoLoadSuiteId(null)
      return
    }

    if (requestedSuiteIdRef.current !== requestedSuiteId) {
      requestedSuiteIdRef.current = requestedSuiteId
      setAutoLoadSuiteId(requestedSuiteId)
    }
  }, [requestedSuiteId])

  const handleSelectSuite = useCallback(
    async (suiteId: number) => {
      const suite = suites.find((item) => item.id === suiteId)
      if (!suite) {
        toast.error('Selected suite could not be found')
        return
      }

      setLoadingData(true)
      setLoadDialogOpen(false)
      try {
        const response = await fetchAnalyticsSuiteData(suiteId)
        setSelectedSuite(suite)
        setSuiteData(response)
        setSelectedCsvOptions([])
        setSearchParams({ suiteId: String(suiteId) }, { replace: true })
        toast.success(`Loaded analytics for "${suite.name}"`)
      } catch (error) {
        console.error('Failed to fetch analytics data', error)
        toast.error('Unable to load analytics data for the selected suite')
      } finally {
        setLoadingData(false)
      }
    },
    [setSearchParams, suites],
  )

  useEffect(() => {
    if (autoLoadSuiteId === null) {
      return
    }

    const targetSuite = suites.find((item) => item.id === autoLoadSuiteId)
    if (!targetSuite) {
      if (!suitesLoading) {
        toast.error('Selected suite could not be found')
        setAutoLoadSuiteId(null)
      }
      return
    }

    void handleSelectSuite(autoLoadSuiteId)
    setAutoLoadSuiteId(null)
  }, [autoLoadSuiteId, handleSelectSuite, suites, suitesLoading])

  const exportSeries = useMemo<ExportSeriesDefinition[]>(() => {
    if (!suiteData) return []

    const series: ExportSeriesDefinition[] = []

    const addSeries = (label: string, values: number[]) => {
      if (!values || values.length === 0) return
      series.push({
        option: { id: label, label },
        values,
      })
    }

    const normalizeLabel = (experiment: AnalyticsExperiment) =>
      experiment.name || experiment.key

    suiteData.experiments.forEach((experiment) => {
      const baseLabel = normalizeLabel(experiment)

      if (experiment.training) {
        const { training } = experiment
        if (training.reward?.length) {
          addSeries(`${baseLabel} • Training • Reward`, training.reward)
        }
        Object.entries(training.actions ?? {}).forEach(([key, values]) => {
          addSeries(`${baseLabel} • Training • Action • ${key}`, values)
        })
        Object.entries(training.states ?? {}).forEach(([key, values]) => {
          addSeries(`${baseLabel} • Training • State • ${key}`, values)
        })
      }

      if (experiment.evaluation) {
        const { evaluation } = experiment
        evaluation.episodes.forEach((episode, index) => {
          const episodeLabel =
            episode.label || `Episode ${index + 1}` || `Episode ${episode.id}`
          if (episode.reward?.length) {
            addSeries(
              `${baseLabel} • Evaluation • ${episodeLabel} • Reward`,
              episode.reward,
            )
          }
          Object.entries(episode.actions ?? {}).forEach(([key, values]) => {
            addSeries(
              `${baseLabel} • Evaluation • ${episodeLabel} • Action • ${key}`,
              values,
            )
          })
          Object.entries(episode.states ?? {}).forEach(([key, values]) => {
            addSeries(
              `${baseLabel} • Evaluation • ${episodeLabel} • State • ${key}`,
              values,
            )
          })
        })
      }
    })

    return series
  }, [suiteData])

  const csvOptions = useMemo<CsvOption[]>(
    () => exportSeries.map((series) => series.option),
    [exportSeries],
  )

  const seriesLookup = useMemo(() => {
    const map = new Map<string, number[]>()
    exportSeries.forEach(({ option, values }) => {
      map.set(option.id, values)
    })
    return map
  }, [exportSeries])

  const handleToggleCsvOption = useCallback((id: string) => {
    setSelectedCsvOptions((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    )
  }, [])

  const handleExportCsv = useCallback(() => {
    if (selectedCsvOptions.length === 0) {
      toast.error('Select at least one dataset to export')
      return
    }

    const selectedSeries = selectedCsvOptions
      .map((id) => ({ id, values: seriesLookup.get(id) ?? [], label: id }))
      .filter((item) => item.values.length > 0)

    if (selectedSeries.length === 0) {
      toast.error('The selected datasets do not contain any values')
      return
    }

    const maxLength = Math.max(
      ...selectedSeries.map((item) => item.values.length),
    )
    const header = ['Step', ...selectedSeries.map((item) => item.label)]
    const rows = [header]

    for (let index = 0; index < maxLength; index += 1) {
      const row = [
        escapeCsvValue(index + 1),
        ...selectedSeries.map((item) =>
          escapeCsvValue(item.values[index] ?? undefined),
        ),
      ]
      rows.push(row)
    }

    const csvContent = rows.map((row) => row.join(',')).join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = window.URL.createObjectURL(blob)
    const anchor = document.createElement('a')

    const baseName = suiteData?.file_name?.replace(/\.h5$/i, '')
    anchor.href = url
    anchor.download = `${baseName || 'analytics'}-export.csv`
    anchor.click()
    window.URL.revokeObjectURL(url)
    setCsvDialogOpen(false)
  }, [selectedCsvOptions, seriesLookup, suiteData?.file_name])

  const handleDownloadHdf5 = useCallback(async () => {
    if (!selectedSuite) {
      toast.error('Load an experiment suite before downloading the export')
      return
    }

    try {
      const { blob, fileName } = await downloadAnalyticsSuiteFile(
        selectedSuite.id,
      )
      const url = window.URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = fileName
      anchor.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to download analytics export', error)
      toast.error('Unable to download the HDF5 export for this suite')
    }
  }, [selectedSuite])

  const renderExperiment = (experiment: AnalyticsExperiment, index: number) => {
    const evaluation = experiment.evaluation
    const training = experiment.training
    const experimentName = experiment.name || experiment.key

    return (
      <section
        key={experiment.key}
        className="bg-card/40 flex flex-col gap-6 rounded-xl border p-6 shadow-sm"
      >
        <div className="flex flex-col gap-1">
          <h2 className="text-xl font-semibold">
            Experiment {index + 1}: {experimentName}
          </h2>
          {experiment.metadata &&
            Object.keys(experiment.metadata).length > 0 && (
              <p className="text-muted-foreground text-sm">
                {Object.entries(experiment.metadata)
                  .map(([key, value]) => `${key}: ${String(value)}`)
                  .join(' • ')}
              </p>
            )}
        </div>

        {evaluation && (
          <div className="flex flex-col gap-4">
            <h3 className="text-lg font-semibold">Evaluation</h3>
            {evaluation.episodes.length === 0 && (
              <div className="text-muted-foreground rounded-md border border-dashed p-4 text-sm">
                No evaluation episodes were recorded for this experiment.
              </div>
            )}
            {evaluation.episodes.map((episode, episodeIndex) => (
              <DatasetViewer
                key={`${experiment.key}-evaluation-${episode.id}`}
                title={`Episode ${episodeIndex + 1}${
                  episode.label ? ` • ${episode.label}` : ''
                }`}
                reward={episode.reward}
                actions={episode.actions}
                states={episode.states}
                metadata={episode.metadata}
                emptyMessage="No data recorded for this episode."
              />
            ))}
          </div>
        )}

        {training && (
          <div className="flex flex-col gap-4">
            <h3 className="text-lg font-semibold">Training</h3>
            <DatasetViewer
              title="Training Summary"
              reward={training.reward}
              actions={training.actions}
              states={training.states}
              metadata={training.metadata}
              emptyMessage="No training data recorded for this experiment."
            />
          </div>
        )}
      </section>
    )
  }

  return (
    <CustomPage>
      <div className="flex flex-col gap-6 pt-4">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-bold">Experiment Analytics</h1>
            {selectedSuite && (
              <p className="mt-2 text-sm">
                Loaded suite:{' '}
                <span className="font-semibold">{selectedSuite.name}</span> (ID{' '}
                {selectedSuite.id})
              </p>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={() => setLoadDialogOpen(true)} className="gap-2">
              <RefreshCw className="size-4" /> Load Data
            </Button>
            <Button
              variant="outline"
              className="gap-2"
              onClick={() => setCsvDialogOpen(true)}
              disabled={!suiteData || exportSeries.length === 0}
            >
              Export CSV
            </Button>
            <Button
              variant="outline"
              className="gap-2"
              onClick={handleDownloadHdf5}
              disabled={!selectedSuite}
            >
              <FileDown className="size-4" /> Download .h5
            </Button>
          </div>
        </div>

        {loadingData && (
          <div className="text-muted-foreground flex items-center gap-3 rounded-lg border border-dashed p-6">
            <Loader2 className="size-5 animate-spin" /> Loading analytics
            data...
          </div>
        )}

        {!loadingData && !suiteData && (
          <div className="text-muted-foreground rounded-lg border border-dashed p-6 text-sm">
            Load experiment analytics to explore the recorded training and
            evaluation metrics. Use the “Load Data” button above to get started.
          </div>
        )}

        {!loadingData && suiteData && suiteData.experiments.length === 0 && (
          <div className="text-muted-foreground rounded-lg border border-dashed p-6 text-sm">
            No experiments were found in the exported analytics data.
          </div>
        )}

        {!loadingData && suiteData && suiteData.experiments.length > 0 && (
          <div className="flex flex-col gap-6">
            {suiteData.experiments.map((experiment, index) =>
              renderExperiment(experiment, index),
            )}
          </div>
        )}
      </div>

      <LoadDataDialog
        open={loadDialogOpen}
        onOpenChange={setLoadDialogOpen}
        suites={suites}
        loading={suitesLoading}
        onRefresh={loadSuites}
        onSelectSuite={handleSelectSuite}
      />

      <CsvExportDialog
        open={csvDialogOpen}
        onOpenChange={setCsvDialogOpen}
        options={csvOptions}
        selected={selectedCsvOptions}
        onToggle={handleToggleCsvOption}
        onExport={handleExportCsv}
      />
    </CustomPage>
  )
}

export default Analytics
