import { useEffect, useState } from 'react'
import type { AxiosError } from 'axios'

import { fetchExperimentSuiteLogs } from '@/services/experiment-service.ts'

import { splitLines } from '../utils.ts'

interface UseCompletedLogsOptions {
  suiteId?: number
}

interface UseCompletedLogsResult {
  completedLogsOpen: boolean
  completedLogLines: string[]
  completedLogsLoading: boolean
  completedLogsError: string | null
  handleCompletedLogsOpenChange: (open: boolean) => void
}

export const useCompletedLogs = ({
  suiteId,
}: UseCompletedLogsOptions): UseCompletedLogsResult => {
  const [completedLogsOpen, setCompletedLogsOpen] = useState(false)
  const [completedLogLines, setCompletedLogLines] = useState<string[]>([])
  const [completedLogsLoading, setCompletedLogsLoading] = useState(false)
  const [completedLogsError, setCompletedLogsError] = useState<string | null>(null)

  useEffect(() => {
    if (!completedLogsOpen) {
      return
    }

    if (typeof suiteId !== 'number') {
      setCompletedLogLines([])
      setCompletedLogsError('Logs are only available for saved experiment suites')
      setCompletedLogsLoading(false)
      return
    }

    let ignore = false
    setCompletedLogsLoading(true)
    setCompletedLogsError(null)

    fetchExperimentSuiteLogs(suiteId)
      .then(({ content }) => {
        if (ignore) return
        setCompletedLogLines(splitLines(content))
      })
      .catch((error: unknown) => {
        if (ignore) return
        const responseStatus = (error as AxiosError)?.response?.status
        if (responseStatus === 404) {
          setCompletedLogLines([])
          setCompletedLogsError('Log file could not be found for this suite')
        } else {
          console.error('Failed to load completed logs', error)
          setCompletedLogsError('Unable to load logs for this suite')
        }
      })
      .finally(() => {
        if (!ignore) {
          setCompletedLogsLoading(false)
        }
      })

    return () => {
      ignore = true
    }
  }, [completedLogsOpen, suiteId])

  const handleCompletedLogsOpenChange = (open: boolean) => {
    setCompletedLogsOpen(open)
    if (!open) {
      setCompletedLogsError(null)
    }
  }

  return {
    completedLogsOpen,
    completedLogLines,
    completedLogsLoading,
    completedLogsError,
    handleCompletedLogsOpenChange,
  }
}
