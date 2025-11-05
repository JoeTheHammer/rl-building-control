import React, { useMemo } from 'react'

import { Progress } from '@/components/ui/progress.tsx'
import type { ExperimentProgressResponse } from '@/services/experiment-service.ts'

interface StatusSummaryProps {
  progress: ExperimentProgressResponse | null
  loading: boolean
  error?: string | null
}

const computePercentage = (current?: number, total?: number): number => {
  if (typeof current !== 'number' || typeof total !== 'number' || total <= 0) {
    return 0
  }
  return Math.min(100, Math.max(0, (current / total) * 100))
}

const formatEpisodes = (current?: number, total?: number): string => {
  const safeCurrent = typeof current === 'number' ? Math.max(current, 0) : 0
  const safeTotal = typeof total === 'number' ? Math.max(total, 0) : 0
  if (safeTotal <= 0) {
    return `${safeCurrent}`
  }
  return `${safeCurrent} / ${safeTotal}`
}

const StatusSummary: React.FC<StatusSummaryProps> = ({
  progress,
  loading,
  error,
}) => {
  const trainingPercent = useMemo(
    () =>
      computePercentage(
        progress?.current_training_episode,
        progress?.total_training_episodes,
      ),
    [progress?.current_training_episode, progress?.total_training_episodes],
  )

  const evaluationPercent = useMemo(
    () =>
      computePercentage(
        progress?.current_evaluation_episode,
        progress?.total_evaluation_episodes,
      ),
    [progress?.current_evaluation_episode, progress?.total_evaluation_episodes],
  )

  const hasTraining = useMemo(
    () =>
      typeof progress?.current_training_episode === 'number' ||
      typeof progress?.total_training_episodes === 'number',
    [progress?.current_training_episode, progress?.total_training_episodes],
  )

  const hasEvaluation = useMemo(
    () =>
      typeof progress?.current_evaluation_episode === 'number' ||
      typeof progress?.total_evaluation_episodes === 'number',
    [
      progress?.current_evaluation_episode,
      progress?.total_evaluation_episodes,
    ],
  )

  if (loading) {
    return (
      <div className="bg-muted/60 text-muted-foreground rounded-md p-3 text-[11px] font-medium">
        Updating status…
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-destructive/10 text-destructive rounded-md p-3 text-[11px] font-medium">
        {error}
      </div>
    )
  }

  if (!progress) {
    return null
  }

  return (
    <div className="border-border/40 bg-background/60 flex flex-col gap-2 rounded-md border p-3 text-xs">
      <div className="flex items-center justify-between text-[11px] font-semibold uppercase tracking-wide">
        <span>Current status</span>
        <span>{progress.status ?? 'Pending'}</span>
      </div>

      {hasTraining && (
        <div className="space-y-1">
          <div className="flex items-center justify-between text-[11px]">
            <span>Training</span>
            <span>{formatEpisodes(progress.current_training_episode, progress.total_training_episodes)}</span>
          </div>
          <Progress value={trainingPercent} className="h-1.5" />
        </div>
      )}

      {hasEvaluation && (
        <div className="space-y-1">
          <div className="flex items-center justify-between text-[11px]">
            <span>Evaluation</span>
            <span>{formatEpisodes(progress.current_evaluation_episode, progress.total_evaluation_episodes)}</span>
          </div>
          <Progress value={evaluationPercent} className="h-1.5" />
        </div>
      )}
    </div>
  )
}

export default StatusSummary
