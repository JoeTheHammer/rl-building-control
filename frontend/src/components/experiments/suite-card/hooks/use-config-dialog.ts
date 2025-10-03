import { useCallback, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import type { ExperimentConfigDetailsResponse } from '@/services/experiment-service.ts'

export type ActiveConfigState =
  | { type: 'experiment' }
  | { type: 'environment'; experimentId: number }
  | { type: 'controller'; experimentId: number }
  | null

interface UseConfigDialogOptions {
  configDetails: ExperimentConfigDetailsResponse | null
  configName?: string
  setConfigError: React.Dispatch<React.SetStateAction<string | null>>
}

interface UseConfigDialogResult {
  activeConfig: ActiveConfigState
  openConfigDialog: (config: Exclude<ActiveConfigState, null>) => void
  handleDialogOpenChange: (open: boolean) => void
  handleEdit: () => void
  activeSection: unknown
  dialogTitle: string
}

export const useConfigDialog = ({
  configDetails,
  configName,
  setConfigError,
}: UseConfigDialogOptions): UseConfigDialogResult => {
  const navigate = useNavigate()
  const [activeConfig, setActiveConfig] = useState<ActiveConfigState>(null)

  const openConfigDialog = useCallback(
    (config: Exclude<ActiveConfigState, null>) => {
      if (!configName) {
        setConfigError('No configuration file associated with this suite')
        setActiveConfig(null)
        return
      }
      setConfigError(null)
      setActiveConfig(config)
    },
    [configName, setConfigError],
  )

  const handleDialogOpenChange = useCallback((open: boolean) => {
    if (!open) {
      setActiveConfig(null)
    }
  }, [])

  const handleEdit = useCallback(() => {
    if (!activeConfig || !configDetails) {
      setActiveConfig(null)
      return
    }

    if (activeConfig.type === 'experiment' && configDetails.experiment) {
      navigate('/experiment-configurator', {
        state: { initialExperimentConfig: configDetails.experiment },
      })
    } else if (activeConfig.type === 'environment') {
      const entry = configDetails.experiments?.find(
        (item) => item.id === activeConfig.experimentId,
      )
      if (entry?.environment) {
        navigate('/environment-configurator', {
          state: { initialEnvironmentConfig: entry.environment },
        })
      }
    } else if (activeConfig.type === 'controller') {
      const entry = configDetails.experiments?.find(
        (item) => item.id === activeConfig.experimentId,
      )
      if (entry?.controller) {
        navigate('/controller-configurator', {
          state: { initialControllerConfig: entry.controller },
        })
      }
    }
    setActiveConfig(null)
  }, [activeConfig, configDetails, navigate])

  const activeSection = useMemo(() => {
    if (!activeConfig || !configDetails) {
      return null
    }
    if (activeConfig.type === 'experiment') {
      return configDetails.experiment ?? null
    }
    const entry = configDetails.experiments?.find(
      (item) => item.id === activeConfig.experimentId,
    )
    if (!entry) {
      return null
    }
    if (activeConfig.type === 'environment') {
      return entry.environment ?? null
    }
    return entry.controller ?? null
  }, [activeConfig, configDetails])

  const dialogTitle = useMemo(() => {
    if (!activeConfig) {
      return ''
    }
    const base =
      activeConfig.type === 'experiment'
        ? 'Experiment'
        : activeConfig.type === 'environment'
          ? 'Environment'
          : 'Controller'
    if (activeConfig.type === 'experiment') {
      return base
    }
    const entry = configDetails?.experiments?.find(
      (item) => item.id === activeConfig.experimentId,
    )
    const name = entry?.name ?? `Experiment ${activeConfig.experimentId}`
    return `${base} – ${name}`
  }, [activeConfig, configDetails])

  return {
    activeConfig,
    openConfigDialog,
    handleDialogOpenChange,
    handleEdit,
    activeSection,
    dialogTitle,
  }
}
