import React, { useEffect, useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  Brush,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Info } from 'lucide-react'

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select.tsx'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table.tsx'
import { Slider } from '@/components/ui/slider'

type DatasetType = 'reward' | 'actions' | 'states' | 'measurements'
type ViewMode = 'line' | 'bar' | 'table'

interface DatasetViewerProps {
  title: string
  reward?: number[]
  actions?: Record<string, number[]>
  states?: Record<string, number[]>
  measurements?: Record<string, number[]>
  metadata?: Record<string, unknown>
  emptyMessage?: string
}

const viewModeOptions: { value: ViewMode; label: string }[] = [
  { value: 'line', label: 'Line chart' },
  { value: 'bar', label: 'Bar chart' },
  { value: 'table', label: 'Table view' },
]

const avgOptions = [
  { value: '1', label: 'No averaging (all points)' },
  { value: '5', label: 'Average every 5 points' },
  { value: '10', label: 'Average every 10 points' },
  { value: '20', label: 'Average every 20 points' },
  { value: '50', label: 'Average every 50 points' },
  { value: '100', label: 'Average every 100 points' },
  { value: '200', label: 'Average every 200 points' },
  { value: '500', label: 'Average every 500 points' },
]

const DatasetViewer: React.FC<DatasetViewerProps> = ({
  title,
  reward,
  actions,
  states,
  measurements,
  metadata,
  emptyMessage,
}) => {
  const hasReward = Array.isArray(reward) && reward.length > 0
  const availableActions = useMemo(
    () => Object.entries(actions ?? {}).filter(([, v]) => v.length > 0),
    [actions],
  )
  const availableStates = useMemo(
    () => Object.entries(states ?? {}).filter(([, v]) => v.length > 0),
    [states],
  )
  const availableMeasurements = useMemo(
    () => Object.entries(measurements ?? {}).filter(([, v]) => v.length > 0),
    [measurements],
  )

  const firstAvailableType: DatasetType | null = useMemo(() => {
    if (hasReward) return 'reward'
    if (availableActions.length > 0) return 'actions'
    if (availableStates.length > 0) return 'states'
    if (availableMeasurements.length > 0) return 'measurements'
    return null
  }, [hasReward, availableActions, availableStates, availableMeasurements])

  const [datasetType, setDatasetType] = useState<DatasetType>('reward')
  const [seriesKey, setSeriesKey] = useState<string>('')
  const [viewMode, setViewMode] = useState<ViewMode>('line')
  const [avgWindow, setAvgWindow] = useState<number>(10)

  // ---- Manual Y-axis range state ----
  const [manualYRange, setManualYRange] = useState(false)
  const [yRange, setYRange] = useState<[number, number]>([0, 0])

  useEffect(() => {
    if (firstAvailableType) {
      setDatasetType(firstAvailableType)
      if (firstAvailableType === 'actions' && availableActions.length > 0) {
        setSeriesKey(availableActions[0][0])
      } else if (
        firstAvailableType === 'states' &&
        availableStates.length > 0
      ) {
        setSeriesKey(availableStates[0][0])
      } else if (
        firstAvailableType === 'measurements' &&
        availableMeasurements.length > 0
      ) {
        setSeriesKey(availableMeasurements[0][0])
      } else {
        setSeriesKey('')
      }
    }
  }, [
    firstAvailableType,
    availableActions,
    availableStates,
    availableMeasurements,
  ])

  useEffect(() => {
    if (datasetType === 'actions' && availableActions.length > 0) {
      if (!availableActions.some(([key]) => key === seriesKey)) {
        setSeriesKey(availableActions[0][0])
      }
    }
    if (datasetType === 'states' && availableStates.length > 0) {
      if (!availableStates.some(([key]) => key === seriesKey)) {
        setSeriesKey(availableStates[0][0])
      }
    }
    if (datasetType === 'measurements' && availableMeasurements.length > 0) {
      if (!availableMeasurements.some(([key]) => key === seriesKey)) {
        setSeriesKey(availableMeasurements[0][0])
      }
    }
    if (datasetType === 'reward') {
      setSeriesKey('')
    }
  }, [
    datasetType,
    seriesKey,
    availableActions,
    availableStates,
    availableMeasurements,
  ])

  const dataValues: number[] | null = useMemo(() => {
    if (datasetType === 'reward') return hasReward ? (reward ?? []) : null
    if (datasetType === 'actions')
      return (
        availableActions.find(([k]) => k === seriesKey)?.[1] ??
        availableActions[0]?.[1] ??
        null
      )
    if (datasetType === 'states')
      return (
        availableStates.find(([k]) => k === seriesKey)?.[1] ??
        availableStates[0]?.[1] ??
        null
      )
    if (datasetType === 'measurements')
      return (
        availableMeasurements.find(([k]) => k === seriesKey)?.[1] ??
        availableMeasurements[0]?.[1] ??
        null
      )
    return null
  }, [
    datasetType,
    reward,
    hasReward,
    availableActions,
    availableStates,
    availableMeasurements,
    seriesKey,
  ])

  const chartData = useMemo(() => {
    if (!dataValues) return []
    if (avgWindow <= 1)
      return dataValues.map((v, i) => ({ index: i + 1, value: Number(v) }))
    const averaged: { index: number; value: number }[] = []
    for (let i = 0; i < dataValues.length; i += avgWindow) {
      const chunk = dataValues.slice(i, i + avgWindow)
      const avg = chunk.reduce((a, b) => a + b, 0) / chunk.length
      averaged.push({ index: i + 1, value: avg })
    }
    return averaged
  }, [dataValues, avgWindow])

  // Initialize Y range when chartData changes
  useEffect(() => {
    if (chartData.length > 0) {
      const minVal = Math.min(...chartData.map((d) => d.value))
      const maxVal = Math.max(...chartData.map((d) => d.value))
      const min = Math.min(minVal, 0)
      const max = Math.max(maxVal, 0) * 1.2 // add 20% buffer
      setYRange([min, max])
    }
  }, [chartData])

  const visibleData = useMemo(() => {
    if (!manualYRange) return chartData
    const [min, max] = yRange
    return chartData.filter((d) => d.value >= min && d.value <= max)
  }, [chartData, manualYRange, yRange])

  const renderChart = () => {
    if (!chartData.length)
      return (
        <div className="flex min-h-40 items-center justify-center rounded-md border border-dashed">
          <span className="text-muted-foreground text-sm">
            {emptyMessage ?? 'No data available for the selected series.'}
          </span>
        </div>
      )

    if (viewMode === 'table')
      return (
        <div className="max-h-80 overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Step</TableHead>
                <TableHead>Value</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {visibleData.map((d, i) => (
                <TableRow key={i}>
                  <TableCell>{d.index}</TableCell>
                  <TableCell>{d.value.toFixed(4)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )

    const ChartComponent = viewMode === 'bar' ? BarChart : LineChart
    const minVal = Math.min(...chartData.map((d) => d.value))
    const maxVal = Math.max(...chartData.map((d) => d.value))
    const globalMin = Math.min(minVal, 0)
    const globalMax = Math.max(maxVal, 0) * 1.2

    return (
      <div className="relative w-full space-y-3">
        {/* --- Y-Range Controls --- */}
        <div className="border-border/50 flex items-center justify-end gap-4 border-t py-2">
          <button
            onClick={() => setManualYRange((prev) => !prev)}
            className={`rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
              manualYRange
                ? 'bg-primary text-primary-foreground border-primary'
                : 'bg-background text-muted-foreground hover:bg-accent'
            } `}
          >
            {manualYRange ? 'Auto Y-range' : 'Manual Y-range'}
          </button>

          {manualYRange && (
            <div className="text-muted-foreground flex flex-wrap items-center gap-5 text-xs">
              <div className="flex w-48 flex-col">
                <label className="mb-1 font-medium">
                  Y-min ({yRange[0].toFixed(2)})
                </label>
                <Slider
                  className="cursor-pointer"
                  min={globalMin}
                  max={globalMax}
                  step={(globalMax - globalMin) / 100}
                  value={[yRange[0]]}
                  onValueChange={([val]) =>
                    setYRange([Math.min(val, yRange[1] - 0.01), yRange[1]])
                  }
                />
              </div>

              <div className="flex w-48 flex-col">
                <label className="mb-1 font-medium">
                  Y-max ({yRange[1].toFixed(2)})
                </label>
                <Slider
                  className="cursor-pointer"
                  min={globalMin}
                  max={globalMax}
                  step={(globalMax - globalMin) / 100}
                  value={[yRange[1]]}
                  onValueChange={([val]) =>
                    setYRange([yRange[0], Math.max(val, yRange[0] + 0.01)])
                  }
                />
              </div>
            </div>
          )}
        </div>

        {/* --- Chart --- */}
        <div className="h-96 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ChartComponent data={visibleData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="index" tickLine={false} />
              <YAxis
                domain={
                  manualYRange ? [yRange[0], yRange[1]] : ['auto', 'auto']
                }
                tickLine={false}
                tickFormatter={(v) => v.toFixed(1)}
              />
              <Tooltip formatter={(v) => Number(v).toFixed(2)} />
              <Brush dataKey="index" height={20} stroke="hsl(var(--primary))" />
              {viewMode === 'bar' ? (
                <Bar dataKey="value" fill="hsl(var(--primary))" />
              ) : (
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#49474C"
                  strokeWidth={1}
                  dot={false}
                  isAnimationActive={false}
                />
              )}
            </ChartComponent>
          </ResponsiveContainer>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-card space-y-4 rounded-lg border p-4 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-col gap-1">
          <h3 className="text-lg font-semibold">{title}</h3>
          {metadata && Object.keys(metadata).length > 0 && (
            <div className="text-muted-foreground flex flex-wrap items-center gap-2 text-xs">
              <Info className="size-3" />
              {Object.entries(metadata).map(([k, v]) => (
                <span key={k} className="bg-muted rounded-full px-2 py-0.5">
                  {k}: {String(v)}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* --- Top controls --- */}
        <div className="grid w-full max-w-lg grid-cols-2 gap-3">
          <Select
            value={datasetType}
            onValueChange={(v) => setDatasetType(v as DatasetType)}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select data" />
            </SelectTrigger>
            <SelectContent className="bg-background">
              <SelectItem value="reward" disabled={!hasReward}>
                Reward
              </SelectItem>
              <SelectItem
                value="actions"
                disabled={availableActions.length === 0}
              >
                Actions
              </SelectItem>
              <SelectItem
                value="states"
                disabled={availableStates.length === 0}
              >
                States
              </SelectItem>
              <SelectItem
                value="measurements"
                disabled={availableMeasurements.length === 0}
              >
                Measurements
              </SelectItem>
            </SelectContent>
          </Select>

          {(datasetType === 'actions' ||
            datasetType === 'states' ||
            datasetType === 'measurements') && (
            <Select value={seriesKey} onValueChange={setSeriesKey}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select series" />
              </SelectTrigger>
              <SelectContent className="bg-background">
                {(datasetType === 'actions'
                  ? availableActions
                  : datasetType === 'states'
                    ? availableStates
                    : availableMeasurements
                ).map(([key]) => (
                  <SelectItem key={key} value={key}>
                    {key}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          <Select
            value={avgWindow.toString()}
            onValueChange={(v) => setAvgWindow(Number(v))}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Averaging window" />
            </SelectTrigger>
            <SelectContent className="bg-background">
              {avgOptions.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={viewMode}
            onValueChange={(v) => setViewMode(v as ViewMode)}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="View mode" />
            </SelectTrigger>
            <SelectContent className="bg-background">
              {viewModeOptions.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {renderChart()}
    </div>
  )
}

export default DatasetViewer
