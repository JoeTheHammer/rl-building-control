import React, { useEffect, useRef, useState } from 'react'
import { BarChart3, ChevronDown, ChevronUp, Power } from 'lucide-react'

import { Badge } from '@/components/ui/badge.tsx'
import { Button } from '@/components/ui/button.tsx'
import { CardDescription, CardTitle } from '@/components/ui/card.tsx'
import { CollapsibleTrigger } from '@/components/ui/collapsible.tsx'
import { cn } from '@/lib/utils.ts'
import type { ExperimentSuiteStatus } from '@/services/experiment-service.ts'

import type { Suite, TensorboardControls } from './types.ts'
import { getStatusBadgeClass } from './utils.ts'

interface HeaderSectionProps {
  suite: Suite
  status: ExperimentSuiteStatus
  fileName: string
  fullPath?: string
  idLabel?: string
  actions: React.ReactNode
  detailsOpen: boolean
  tensorboard?: TensorboardControls | null
}

const HeaderSection: React.FC<HeaderSectionProps> = ({
  suite,
  status,
  fileName,
  fullPath,
  idLabel,
  actions,
  detailsOpen,
  tensorboard,
}) => {
  const showTensorboardRow = Boolean(tensorboard)
  const isTensorboardRunning = tensorboard?.isRunning ?? false

  const actionsRowRef = useRef<HTMLDivElement | null>(null)
  const [actionsRowWidth, setActionsRowWidth] = useState<number | null>(null)

  useEffect(() => {
    const node = actionsRowRef.current
    if (!node) return

    const updateWidth = () => {
      setActionsRowWidth(node.offsetWidth)
    }

    updateWidth()

    if (typeof ResizeObserver !== 'undefined') {
      const observer = new ResizeObserver(() => updateWidth())
      observer.observe(node)
      return () => observer.disconnect()
    }

    if (typeof window !== 'undefined') {
      window.addEventListener('resize', updateWidth)
      return () => window.removeEventListener('resize', updateWidth)
    }

    return undefined
  }, [actions, detailsOpen])

  return (
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

      <div className="flex w-full flex-col gap-2 md:w-auto md:items-end">
        <div ref={actionsRowRef} className="flex flex-wrap justify-end gap-2">
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

        {showTensorboardRow && (
          <div
            className="flex flex-wrap justify-end gap-2"
            style={
              actionsRowWidth
                ? { width: `${actionsRowWidth}px` }
                : undefined
            }
          >
            <Button
              onClick={tensorboard?.onOpen}
              disabled={tensorboard?.disabled ?? true}
              aria-busy={tensorboard?.isLoading}
              className={cn(
                'gap-2 justify-center',
                actionsRowWidth && isTensorboardRunning ? 'flex-1' : '',
              )}
            >
              <BarChart3 className="size-4" /> Open TensorBoard
            </Button>
            {isTensorboardRunning ? (
              <Button
                onClick={tensorboard.onStop}
                disabled={tensorboard.isStopping}
                aria-busy={tensorboard.isStopping}
                className={cn(
                  'gap-2 justify-center',
                  actionsRowWidth ? 'flex-1' : '',
                )}
              >
                <Power className="size-4" /> Stop TensorBoard
              </Button>
            ) : null}
          </div>
        )}
      </div>
    </div>
  )
}

export default HeaderSection
