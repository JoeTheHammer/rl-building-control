import { useEffect, useMemo, useState } from 'react'
import type { AxiosError } from 'axios'

import {
  fetchExperimentSuiteStatus,
  type ExperimentRunStatusResponse,
  type ExperimentSuiteStatus,
} from '@/services/experiment-service.ts'

import { buildProgressById } from '../utils.ts'

interface UseSuiteStatusOptions {
  suiteId?: number
  detailsOpen: boolean
  status: ExperimentSuiteStatus
}

interface UseSuiteStatusResult {
  shouldStreamLogs: boolean
  statusInfo: ExperimentRunStatusResponse | null
  statusLoading: boolean
  statusError: string | null
  progressById: Map<number, ExperimentRunStatusResponse['experiments'][number]>
  hasStatusEntries: boolean
}

export const useSuiteStatus = ({
  suiteId,
  detailsOpen,
  status,
}: UseSuiteStatusOptions): UseSuiteStatusResult => {
  const shouldLoadStatus = status === 'Running' && typeof suiteId === 'number'
  const shouldStreamLogs = shouldLoadStatus && detailsOpen

  const [statusInfo, setStatusInfo] =
    useState<ExperimentRunStatusResponse | null>(null)
  const [statusLoading, setStatusLoading] = useState(false)
  const [statusError, setStatusError] = useState<string | null>(null)

  useEffect(() => {
    if (!shouldLoadStatus || typeof suiteId !== 'number') {
      setStatusInfo(null)
      setStatusError(null)
      setStatusLoading(false)
      return
    }

    let ignore = false
    let firstFetch = true

    const fetchStatus = async () => {
      if (firstFetch) {
        setStatusLoading(true)
      }
      try {
        const data = await fetchExperimentSuiteStatus(suiteId)
        if (ignore) return
        setStatusInfo(data)
        setStatusError(null)
      } catch (error: unknown) {
        if (ignore) return
        const responseStatus = (error as AxiosError)?.response?.status
        if (responseStatus === 404) {
          setStatusInfo(null)
          setStatusError(null)
        } else {
          console.error('Failed to load status file', error)
          setStatusError('Unable to read progress information')
        }
      } finally {
        if (!ignore) {
          setStatusLoading(false)
        }
        firstFetch = false
      }
    }

    fetchStatus()
    const interval = window.setInterval(fetchStatus, 2000)

    return () => {
      ignore = true
      window.clearInterval(interval)
    }
  }, [shouldLoadStatus, suiteId])

  const progressById = useMemo(
    () => buildProgressById(statusInfo),
    [statusInfo],
  )

  const hasStatusEntries = (statusInfo?.experiments?.length ?? 0) > 0

  return {
    shouldStreamLogs,
    statusInfo,
    statusLoading,
    statusError,
    progressById,
    hasStatusEntries,
  }
}
