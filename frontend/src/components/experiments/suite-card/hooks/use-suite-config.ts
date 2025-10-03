import { useEffect, useState } from 'react'
import type { AxiosError } from 'axios'

import {
  fetchExperimentConfigDetails,
  type ExperimentConfigDetailsResponse,
} from '@/services/experiment-service.ts'

interface UseSuiteConfigOptions {
  configName?: string
  detailsOpen: boolean
}

interface UseSuiteConfigResult {
  configDetails: ExperimentConfigDetailsResponse | null
  configLoading: boolean
  configError: string | null
  setConfigError: React.Dispatch<React.SetStateAction<string | null>>
}

export const useSuiteConfig = ({
  configName,
  detailsOpen,
}: UseSuiteConfigOptions): UseSuiteConfigResult => {
  const [configDetails, setConfigDetails] =
    useState<ExperimentConfigDetailsResponse | null>(null)
  const [configLoading, setConfigLoading] = useState(false)
  const [configError, setConfigError] = useState<string | null>(null)

  useEffect(() => {
    if (!detailsOpen || !configName) {
      return
    }

    let ignore = false
    setConfigLoading(true)
    setConfigError(null)

    fetchExperimentConfigDetails(configName)
      .then((data) => {
        if (ignore) return
        setConfigDetails(data)
      })
      .catch((error: unknown) => {
        if (ignore) return
        const responseStatus = (error as AxiosError)?.response?.status
        if (responseStatus === 404) {
          setConfigDetails(null)
          setConfigError('Configuration file could not be found')
        } else {
          console.error('Failed to load configuration details', error)
          setConfigError('Unable to load configuration details')
        }
      })
      .finally(() => {
        if (!ignore) {
          setConfigLoading(false)
        }
      })

    return () => {
      ignore = true
    }
  }, [configName, detailsOpen])

  return { configDetails, configLoading, configError, setConfigError }
}
