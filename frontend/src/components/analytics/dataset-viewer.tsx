import React, { useEffect, useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
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

type DatasetType = 'reward' | 'actions' | 'states'
type ViewMode = 'line' | 'bar' | 'table'

interface DatasetViewerProps {
  title: string
  reward?: number[]
  actions?: Record<string, number[]>
  states?: Record<string, number[]>
  metadata?: Record<string, unknown>
  emptyMessage?: string
}

const viewModeOptions: { value: ViewMode; label: string }[] = [
  { value: 'line', label: 'Line chart' },
  { value: 'bar', label: 'Bar chart' },
  { value: 'table', label: 'Table view' },
]

// Averaging window options
const avgOptions = [
  { value: '1', label: 'No averaging (all points)' },
  { value: '5', label: 'Average every 5 points' },
  { value: '10', label: 'Average every 10 points' },
  { value: '20', label: 'Average every 20 points' },
  { value: '50', label: 'Average every 50 points' },
  { value: '100', label: 'Average every 100 points' },
]

const DatasetViewer: React.FC<DatasetViewerProps> = ({
  title,
  reward,
  actions,
  states,
  metadata,
  emptyMessage,
}) => {
  const hasReward = Array.isArray(reward) && reward.length > 0
  const availableActions = useMemo(
    () =>
      Object.entries(actions ?? {}).filter(([, values]) => values.length > 0),
    [actions],
  )
  const availableStates = useMemo(
    () =>
      Object.entries(states ?? {}).filter(([, values]) => values.length > 0),
    [states],
  )

  const firstAvailableType: DatasetType | null = useMemo(() => {
    if (hasReward) return 'reward'
    if (availableActions.length > 0) return 'actions'
    if (availableStates.length > 0) return 'states'
    return null
  }, [hasReward, availableActions, availableStates])

  const [datasetType, setDatasetType] = useState<DatasetType>('reward')
  const [seriesKey, setSeriesKey] = useState<string>('')
  const [viewMode, setViewMode] = useState<ViewMode>('line')
  const [avgWindow, setAvgWindow] = useState<number>(10) // Default: average every 10 points

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
      } else {
        setSeriesKey('')
      }
    }
  }, [firstAvailableType, availableActions, availableStates])

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
    if (datasetType === 'reward') {
      setSeriesKey('')
    }
  }, [datasetType, seriesKey, availableActions, availableStates])

  const dataValues: number[] | null = useMemo(() => {
    if (datasetType === 'reward') {
      return hasReward ? (reward ?? []) : null
    }
    if (datasetType === 'actions') {
      const entry = availableActions.find(([key]) => key === seriesKey)
      return entry ? entry[1] : (availableActions[0]?.[1] ?? null)
    }
    if (datasetType === 'states') {
      const entry = availableStates.find(([key]) => key === seriesKey)
      return entry ? entry[1] : (availableStates[0]?.[1] ?? null)
    }
    return null
  }, [
    datasetType,
    reward,
    hasReward,
    availableActions,
    availableStates,
    seriesKey,
  ])

  // Averaged chart data
  const chartData = useMemo(() => {
    if (!dataValues) return []

    if (avgWindow <= 1) {
      return dataValues.map((v, i) => ({ index: i + 1, value: Number(v) }))
    }

    const averaged: { index: number; value: number }[] = []
    for (let i = 0; i < dataValues.length; i += avgWindow) {
      const chunk = dataValues.slice(i, i + avgWindow)
      const avg = chunk.reduce((a, b) => a + b, 0) / chunk.length
      averaged.push({ index: i + 1, value: avg })
    }
    return averaged
  }, [dataValues, avgWindow])

  const handleDatasetTypeChange = (value: string) => {
    setDatasetType(value as DatasetType)
  }

  const handleSeriesChange = (value: string) => {
    setSeriesKey(value)
  }

  const handleAvgChange = (value: string) => {
    setAvgWindow(parseInt(value))
  }

  const renderChart = () => {
    if (!dataValues || dataValues.length === 0) {
      return (
        <div className="flex min-h-40 items-center justify-center rounded-md border border-dashed">
          <span className="text-muted-foreground text-sm">
            {emptyMessage ?? 'No data available for the selected series.'}
          </span>
        </div>
      )
    }

    if (viewMode === 'table') {
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
              {chartData.map((d, index) => (
                <TableRow key={index}>
                  <TableCell>{d.index}</TableCell>
                  <TableCell>{d.value.toFixed(4)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )
    }

    const ChartComponent = viewMode === 'bar' ? BarChart : LineChart

    return (
      <div className="relative h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ChartComponent data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="index" tickLine={false} />
            <YAxis tickLine={false} domain={['auto', 'auto']} />
            <Tooltip />
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
              {Object.entries(metadata).map(([key, value]) => (
                <span key={key} className="bg-muted rounded-full px-2 py-0.5">
                  {key}: {String(value)}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* dataset type */}
          <Select value={datasetType} onValueChange={handleDatasetTypeChange}>
            <SelectTrigger className="w-40">
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
            </SelectContent>
          </Select>

          {/* series */}
          {(datasetType === 'actions' || datasetType === 'states') && (
            <Select value={seriesKey} onValueChange={handleSeriesChange}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Select series" />
              </SelectTrigger>
              <SelectContent className="bg-background">
                {(datasetType === 'actions'
                  ? availableActions
                  : availableStates
                ).map(([key]) => (
                  <SelectItem key={key} value={key}>
                    {key}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          {/* averaging filter */}
          <Select value={avgWindow.toString()} onValueChange={handleAvgChange}>
            <SelectTrigger className="w-52">
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

          {/* view mode */}
          <Select
            value={viewMode}
            onValueChange={(v) => setViewMode(v as ViewMode)}
          >
            <SelectTrigger className="w-40">
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
