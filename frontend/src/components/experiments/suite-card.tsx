// SuiteCard.tsx
import React from 'react'
import { Info } from 'lucide-react'
import { Badge } from '@/components/ui/badge.tsx'
import { Button } from '@/components/ui/button.tsx'
import {
  Card,
  CardContent,
  CardDescription,
  CardTitle,
} from '@/components/ui/card.tsx'
import { cn } from '@/lib/utils.ts'
import type {
  ExperimentSuiteApiResponse,
  ExperimentSuiteStatus,
} from '@/services/experiment-service.ts'
import type { LocalExperimentSuite } from '@/components/experiments/experiments.tsx'

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

type Suite = LocalExperimentSuite | ExperimentSuiteApiResponse

interface SuiteCardProps {
  suite: Suite
  status: ExperimentSuiteStatus
  idLabel?: string
  actions: React.ReactNode
}

export const SuiteCard: React.FC<SuiteCardProps> = ({
  suite,
  status,
  idLabel,
  actions,
}) => {
  const isLocal = 'localId' in suite
  const fileName = isLocal
    ? getFileName(suite.configName) + '.yaml'
    : getFileName((suite as ExperimentSuiteApiResponse).name) + '.yaml'

  const fullPath =
    !isLocal && (suite as ExperimentSuiteApiResponse).path
      ? (suite as ExperimentSuiteApiResponse).path
      : undefined

  return (
    <Card
      key={isLocal ? suite.localId : suite.id}
      className="border-primary/20"
    >
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

          {/* File name always visible */}
          <CardDescription className="text-muted-foreground text-sm font-medium">
            File: {fileName}
          </CardDescription>

          {/* Show full path only when not local (persisted suite) */}
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

export default SuiteCard
