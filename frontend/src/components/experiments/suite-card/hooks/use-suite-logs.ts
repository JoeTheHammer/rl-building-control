import { useEffect, useRef, useState } from 'react'
import type { AxiosError } from 'axios'

import {
  createExperimentLogEventSource,
  fetchExperimentSuiteLogs,
} from '@/services/experiment-service.ts'

import { mergeLogLines, splitLines } from '../utils.ts'

interface UseSuiteLogsOptions {
  suiteId?: number
  shouldStream: boolean
}

interface UseSuiteLogsResult {
  logLines: string[]
  logLoading: boolean
  logError: string | null
}

export const useSuiteLogs = ({
  suiteId,
  shouldStream,
}: UseSuiteLogsOptions): UseSuiteLogsResult => {
  const [logLines, setLogLines] = useState<string[]>([])
  const [logLoading, setLogLoading] = useState(false)
  const [logError, setLogError] = useState<string | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!shouldStream || typeof suiteId !== 'number') {
      setLogLines([])
      setLogError(null)
      setLogLoading(false)
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
      return
    }

    let ignore = false
    setLogLoading(true)
    setLogError(null)

    fetchExperimentSuiteLogs(suiteId)
      .then(({ content }) => {
        if (ignore) return
        setLogLines(mergeLogLines([], splitLines(content)))
      })
      .catch((error: unknown) => {
        if (ignore) return
        const responseStatus = (error as AxiosError)?.response?.status
        if (responseStatus === 404) {
          setLogLines([])
        } else {
          console.error('Failed to load logs', error)
          setLogError('Unable to load logs')
        }
      })
      .finally(() => {
        if (!ignore) {
          setLogLoading(false)
        }
      })

    if (typeof window !== 'undefined' && 'EventSource' in window) {
      const source = createExperimentLogEventSource(suiteId)
      eventSourceRef.current = source
      source.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as { lines?: string[] }
          if (Array.isArray(payload.lines)) {
            setLogLines((prev) => mergeLogLines(prev, payload.lines ?? []))
          }
        } catch (error) {
          console.error('Failed to parse log stream payload', error)
        }
      }
      source.onerror = () => {
        setLogError((prev) => prev ?? 'Log stream disconnected')
        source.close()
        if (eventSourceRef.current === source) {
          eventSourceRef.current = null
        }
      }
    }

    return () => {
      ignore = true
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [shouldStream, suiteId])

  return { logLines, logLoading, logError }
}
