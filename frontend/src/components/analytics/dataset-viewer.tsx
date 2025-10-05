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

import { Button } from '@/components/ui/button.tsx'
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
    () => Object.entries(actions ?? {}).filter(([, values]) => values.length > 0),
    [actions],
  )
  const availableStates = useMemo(
    () => Object.entries(states ?? {}).filter(([, values]) => values.length > 0),
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

  useEffect(() => {
    if (firstAvailableType) {
      setDatasetType(firstAvailableType)
      if (firstAvailableType === 'actions' && availableActions.length > 0) {
        setSeriesKey(availableActions[0][0])
      } else if (firstAvailableType === 'states' && availableStates.length > 0) {
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
      return hasReward ? reward ?? [] : null
    }
    if (datasetType === 'actions') {
      const entry = availableActions.find(([key]) => key === seriesKey)
      return entry ? entry[1] : availableActions[0]?.[1] ?? null
    }
    if (datasetType === 'states') {
      const entry = availableStates.find(([key]) => key === seriesKey)
      return entry ? entry[1] : availableStates[0]?.[1] ?? null
    }
    return null
  }, [datasetType, reward, hasReward, availableActions, availableStates, seriesKey])

  const chartData = useMemo(
    () =>
      dataValues?.map((value, index) => ({
        index: index + 1,
        value,
      })) ?? [],
    [dataValues],
  )

  const handleDatasetTypeChange = (value: string) => {
    setDatasetType((value as DatasetType) ?? 'reward')
  }

  const handleSeriesChange = (value: string) => {
    setSeriesKey(value)
  }

  const renderChart = () => {
    if (!dataValues || dataValues.length === 0) {
      return (
        <div className="flex min-h-40 items-center justify-center rounded-md border border-dashed">
          <span className="text-sm text-muted-foreground">
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
              {dataValues.map((value, index) => (
                <TableRow key={index}>
                  <TableCell>{index + 1}</TableCell>
                  <TableCell>{value}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )
    }

    if (viewMode === 'bar') {
      return (
        <div className="h-80 w-full">
          <ResponsiveContainer>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="index" tickLine={false} />
              <YAxis tickLine={false} />
              <Tooltip />
              <Bar dataKey="value" fill="hsl(var(--primary))" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )
    }

    return (
      <div className="h-80 w-full">
        <ResponsiveContainer>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="index" tickLine={false} />
            <YAxis tickLine={false} />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="value"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    )
  }

  return (
    <div className="space-y-4 rounded-lg border bg-card p-4 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-col gap-1">
          <h3 className="text-lg font-semibold">{title}</h3>
          {metadata && Object.keys(metadata).length > 0 && (
            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <Info className="size-3" />
              {Object.entries(metadata).map(([key, value]) => (
                <span key={key} className="rounded-full bg-muted px-2 py-0.5">
                  {key}: {String(value)}
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Select value={datasetType} onValueChange={handleDatasetTypeChange}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Select data" />
            </SelectTrigger>
            <SelectContent className="bg-background">
              <SelectItem value="reward" disabled={!hasReward}>
                Reward
              </SelectItem>
              <SelectItem value="actions" disabled={availableActions.length === 0}>
                Actions
              </SelectItem>
              <SelectItem value="states" disabled={availableStates.length === 0}>
                States
              </SelectItem>
            </SelectContent>
          </Select>

          {(datasetType === 'actions' || datasetType === 'states') && (
            <Select value={seriesKey} onValueChange={handleSeriesChange}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Select series" />
              </SelectTrigger>
              <SelectContent className="bg-background">
                {(datasetType === 'actions' ? availableActions : availableStates).map(
                  ([key]) => (
                    <SelectItem key={key} value={key}>
                      {key}
                    </SelectItem>
                  ),
                )}
              </SelectContent>
            </Select>
          )}

          <Select value={viewMode} onValueChange={(value) => setViewMode(value as ViewMode)}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="View mode" />
            </SelectTrigger>
            <SelectContent className="bg-background">
              {viewModeOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {viewMode !== 'table' && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setViewMode(viewMode === 'line' ? 'bar' : 'line')}
            >
              Switch to {viewMode === 'line' ? 'Bar chart' : 'Line chart'}
            </Button>
          )}
        </div>
      </div>

      {renderChart()}
    </div>
  )
}

export default DatasetViewer
