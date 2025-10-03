import React, { useMemo } from 'react'

import { Badge } from '@/components/ui/badge.tsx'
import { Progress } from '@/components/ui/progress.tsx'
import type { ExperimentRunStatusResponse } from '@/services/experiment-service.ts'

interface ProgressSectionProps {
  status: ExperimentRunStatusResponse | null
  loading: boolean
  error?: string | null
}

const formatEpisodes = (current?: number, total?: number): string => {
  if (typeof current !== 'number' && typeof total !== 'number') {
    return 'No data available'
  }
  const safeCurrent = typeof current === 'number' ? Math.max(current, 0) : 0
  const safeTotal = typeof total === 'number' ? Math.max(total, 0) : 0
  if (safeTotal === 0) {
    return `${safeCurrent}`
  }
  return `${safeCurrent} / ${safeTotal}`
}

const computePercentage = (current?: number, total?: number): number => {
  if (typeof current !== 'number' || typeof total !== 'number' || total <= 0) {
    return 0
  }
  return Math.min(100, Math.max(0, (current / total) * 100))
}

const ProgressSection: React.FC<ProgressSectionProps> = ({ status, loading, error }) => {
  const normalizedStatus = status?.status?.toLowerCase()

  const trainingPercent = useMemo(
    () => computePercentage(status?.current_training_episode, status?.total_training_episodes),
    [status?.current_training_episode, status?.total_training_episodes],
  )

  const evaluationPercent = useMemo(
    () =>
      computePercentage(status?.current_evaluation_episode, status?.total_evaluation_episodes),
    [status?.current_evaluation_episode, status?.total_evaluation_episodes],
  )

  if (loading) {
    return <p className="text-muted-foreground text-sm">Loading progress…</p>
  }

  if (error) {
    return <p className="text-destructive text-sm">{error}</p>
  }

  if (!status) {
    return <p className="text-muted-foreground text-sm">Progress information is not available yet.</p>
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={normalizedStatus === 'training' ? 'default' : 'secondary'}>Training</Badge>
        <Badge variant={normalizedStatus === 'evaluation' ? 'default' : 'secondary'}>
          Evaluation
        </Badge>
        {normalizedStatus === 'hyperparameter_tuning' && (
          <Badge variant="outline">Hyperparameter Tuning</Badge>
        )}
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm font-medium">
          <span>Training progress</span>
          <span>{formatEpisodes(status.current_training_episode, status.total_training_episodes)}</span>
        </div>
        <Progress value={trainingPercent} />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm font-medium">
          <span>Evaluation progress</span>
          <span>
            {formatEpisodes(status.current_evaluation_episode, status.total_evaluation_episodes)}
          </span>
        </div>
        <Progress value={evaluationPercent} />
      </div>
    </div>
  )
}

export default ProgressSection
