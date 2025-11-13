import React, { useEffect, useRef, useState } from 'react'
import { BarChart3, ChevronDown, ChevronUp, Power } from 'lucide-react'

import { Badge } from '@/components/ui/badge.tsx'
import { Button } from '@/components/ui/button.tsx'
import { CardDescription, CardTitle } from '@/components/ui/card.tsx'
import { CollapsibleTrigger } from '@/components/ui/collapsible.tsx'
import { cn } from '@/lib/utils.ts'
import type {
  ExperimentProgressResponse,
  ExperimentSuiteStatus,
} from '@/services/experiment-service.ts'

import type { Suite, TensorboardControls } from './types.ts'
import { getStatusBadgeClass } from './utils.ts'
import StatusSummary from './status-summary.tsx'

interface HeaderSectionProps {
  suite: Suite
  status: ExperimentSuiteStatus
  fileName: string
  idLabel?: string
  actions: React.ReactNode
  detailsOpen: boolean
  tensorboard?: TensorboardControls | null
  progressEntries?: ExperimentProgressResponse[]
  statusLoading: boolean
  statusError: string | null
}

const HeaderSection: React.FC<HeaderSectionProps> = ({
  suite,
  status,
  fileName,
  idLabel,
  actions,
  detailsOpen,
  tensorboard,
  progressEntries,
  statusLoading,
  statusError,
}) => {
  const allAreNull = progressEntries?.every((entry) => entry === null) ?? false

  const showTensorboardRow = Boolean(tensorboard)
  const isTensorboardRunning = tensorboard?.isRunning ?? false

  const topRowRef = useRef<HTMLDivElement | null>(null)
  const [topRowWidth, setTopRowWidth] = useState<number | null>(null)

  useEffect(() => {
    const node = topRowRef.current
    if (!node) return

    const updateWidth = () => {
      setTopRowWidth(node.offsetWidth)
    }

    updateWidth()

    if (typeof ResizeObserver !== 'undefined') {
      const observer = new ResizeObserver(() => updateWidth())
      observer.observe(node)
      return () => observer.disconnect()
    }

    window.addEventListener('resize', updateWidth)
    return () => window.removeEventListener('resize', updateWidth)
  }, [])

  return (
    <>
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
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

          {idLabel && (
            <CardDescription className="text-muted-foreground text-sm font-medium">
              {idLabel}
            </CardDescription>
          )}
        </div>

        {/* Actions column */}
        <div className="flex w-full flex-col items-end gap-2">
          {/* Top row: main action buttons */}
          <div
            ref={topRowRef}
            className="flex flex-nowrap items-center justify-end gap-2"
          >
            {actions}

            {showTensorboardRow && !isTensorboardRunning && (
              <Button
                onClick={tensorboard?.onOpen}
                disabled={tensorboard?.disabled ?? true}
                aria-busy={tensorboard?.isLoading}
                className="gap-2"
              >
                <BarChart3 className="size-4" /> Open TensorBoard
              </Button>
            )}

            {showTensorboardRow && isTensorboardRunning && (
              <>
                <Button
                  onClick={tensorboard?.onStop}
                  disabled={tensorboard?.isStopping}
                  aria-busy={tensorboard?.isStopping}
                  className="gap-2"
                >
                  <Power className="size-4" /> Stop TensorBoard
                </Button>

                <Button
                  onClick={tensorboard?.onOpen}
                  disabled={tensorboard?.disabled ?? true}
                  aria-busy={tensorboard?.isLoading}
                  className="gap-2"
                >
                  <BarChart3 className="size-4" /> Open TensorBoard
                </Button>
              </>
            )}
          </div>

          {/* Bottom row: details toggle button matches width of top row */}
          <div
            className="flex justify-end"
            style={topRowWidth ? { width: `${topRowWidth}px` } : undefined}
          >
            <CollapsibleTrigger asChild>
              <Button
                variant="outline"
                className="w-full gap-2"
                disabled={allAreNull && status === 'Running'}
              >
                {detailsOpen ? (
                  <ChevronUp className="size-4" />
                ) : (
                  <ChevronDown className="size-4" />
                )}
                {detailsOpen ? 'Hide details' : 'Show details'}
              </Button>
            </CollapsibleTrigger>
          </div>
        </div>
      </div>
      {status === 'Running' && (
        <div className="mt-2 flex w-full flex-col gap-2">
          {progressEntries?.length ? (
            progressEntries.map((entry) => (
              <StatusSummary
                key={entry.id}
                title={entry.name ?? `Experiment ${entry.id}`}
                progress={entry}
                loading={false}
              />
            ))
          ) : (
            <StatusSummary
              progress={null}
              loading={statusLoading}
              error={statusError}
            />
          )}
        </div>
      )}
    </>
  )
}

export default HeaderSection
