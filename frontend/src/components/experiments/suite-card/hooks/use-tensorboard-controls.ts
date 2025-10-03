import { useCallback, useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'

import {
  EXPERIMENT_API_BASE,
  startTensorBoard,
  stopTensorBoard,
  type StopTensorBoardResponse,
  type TensorBoardStatusResponse,
} from '@/services/experiment-service.ts'

interface UseTensorboardControlsOptions {
  suiteId?: number
  initialStatus: TensorBoardStatusResponse | null
  tensorboardEnabled: boolean
  onTensorboardStatusChange?: (status: TensorBoardStatusResponse) => void
}

interface UseTensorboardControlsResult {
  tensorboardStatus: TensorBoardStatusResponse | null
  canAccessTensorboard: boolean
  openTensorboard: () => Promise<void>
  stopTensorboard: () => Promise<void>
  tensorboardLoading: boolean
  tensorboardStopping: boolean
}

export const useTensorboardControls = ({
  suiteId,
  initialStatus,
  tensorboardEnabled,
  onTensorboardStatusChange,
}: UseTensorboardControlsOptions): UseTensorboardControlsResult => {
  const [tensorboardStatus, setTensorboardStatus] =
    useState<TensorBoardStatusResponse | null>(initialStatus)
  const [tensorboardLoading, setTensorboardLoading] = useState(false)
  const [tensorboardStopping, setTensorboardStopping] = useState(false)

  useEffect(() => {
    setTensorboardStatus(initialStatus)
  }, [initialStatus])

  const canAccessTensorboard = useMemo(
    () => tensorboardEnabled || tensorboardStatus?.enabled === true,
    [tensorboardEnabled, tensorboardStatus?.enabled],
  )

  const updateTensorboardStatus = useCallback(
    (status: TensorBoardStatusResponse) => {
      setTensorboardStatus(status)
      onTensorboardStatusChange?.(status)
    },
    [onTensorboardStatusChange],
  )

  useEffect(() => {
    if (
      typeof window === 'undefined' ||
      typeof navigator === 'undefined' ||
      typeof suiteId !== 'number' ||
      !tensorboardStatus?.running
    ) {
      return
    }

    const endpoint = `${EXPERIMENT_API_BASE}/suites/${suiteId}/tensorboard/stop`

    const handleBeforeUnload = () => {
      try {
        const payload = JSON.stringify({ reason: 'window-unload' })
        const blob = new Blob([payload], { type: 'application/json' })
        navigator.sendBeacon(endpoint, blob)
      } catch (error) {
        console.debug('TensorBoard shutdown beacon failed', error)
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [suiteId, tensorboardStatus?.running])

  const openTensorboard = useCallback(async () => {
    if (typeof suiteId !== 'number') {
      return
    }
    if (!canAccessTensorboard) {
      toast.error('TensorBoard is not enabled for this suite')
      return
    }

    setTensorboardLoading(true)
    try {
      const wasRunning = tensorboardStatus?.running === true
      const status = await startTensorBoard(suiteId, 'ui')

      updateTensorboardStatus(status)

      if (!status.enabled) {
        toast.error('TensorBoard is disabled for this suite')
        return
      }

      if (!wasRunning) {
        toast.success('TensorBoard started')
      }

      if (status.url) {
        window.open(status.url, '_blank', 'noopener,noreferrer')
      } else {
        toast.info('TensorBoard is starting, please try again in a few seconds')
      }
    } catch (error) {
      console.error('Failed to open TensorBoard', error)
      toast.error('Unable to open TensorBoard')
    } finally {
      setTensorboardLoading(false)
    }
  }, [canAccessTensorboard, suiteId, tensorboardStatus?.running, updateTensorboardStatus])

  const stopTensorboardHandler = useCallback(async () => {
    if (typeof suiteId !== 'number') {
      return
    }

    setTensorboardStopping(true)
    try {
      const response: StopTensorBoardResponse = await stopTensorBoard(
        suiteId,
        'user-request',
      )
      updateTensorboardStatus(response)

      if (response.stopped) {
        toast.success('TensorBoard stopped')
      } else {
        toast.info('TensorBoard was not running')
      }
    } catch (error) {
      console.error('Failed to stop TensorBoard', error)
      toast.error('Unable to stop TensorBoard')
    } finally {
      setTensorboardStopping(false)
    }
  }, [suiteId, updateTensorboardStatus])

  return {
    tensorboardStatus,
    canAccessTensorboard,
    openTensorboard,
    stopTensorboard: stopTensorboardHandler,
    tensorboardLoading,
    tensorboardStopping,
  }
}
