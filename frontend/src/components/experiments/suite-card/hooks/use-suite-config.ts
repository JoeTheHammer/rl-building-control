import { useEffect, useState } from 'react'
import type { AxiosError } from 'axios'
import yaml from 'js-yaml'

import {
  fetchExperimentConfigDetails,
  fetchSuiteContext,
  type ExperimentConfigDetailsResponse,
  type SuiteContextFile,
  type SuiteContextResponse,
} from '@/services/experiment-service.ts'

interface UseSuiteConfigOptions {
  configName?: string
  suiteId?: number
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
  suiteId,
  detailsOpen,
}: UseSuiteConfigOptions): UseSuiteConfigResult => {
  const [configDetails, setConfigDetails] =
    useState<ExperimentConfigDetailsResponse | null>(null)
  const [configLoading, setConfigLoading] = useState(false)
  const [configError, setConfigError] = useState<string | null>(null)

  useEffect(() => {
    if (!detailsOpen) {
      return
    }

    let ignore = false
    setConfigLoading(true)
    setConfigError(null)

    const handleError = (error: unknown) => {
      if (ignore) return
      const responseStatus = (error as AxiosError)?.response?.status
      if (responseStatus === 404) {
        setConfigDetails(null)
        setConfigError('Configuration file could not be found')
      } else {
        console.error('Failed to load configuration details', error)
        setConfigError('Unable to load configuration details')
      }
    }

    if (suiteId !== undefined) {
      fetchSuiteContext(suiteId)
        .then((context) => {
          if (ignore) return
          setConfigDetails(convertSuiteContext(context))
        })
        .catch(handleError)
        .finally(() => {
          if (!ignore) {
            setConfigLoading(false)
          }
        })
      return () => {
        ignore = true
      }
    }

    if (!configName) {
      setConfigLoading(false)
      return () => {
        ignore = true
      }
    }

    fetchExperimentConfigDetails(configName)
      .then((data) => {
        if (ignore) return
        setConfigDetails(data)
      })
      .catch(handleError)
      .finally(() => {
        if (!ignore) {
          setConfigLoading(false)
        }
      })

    return () => {
      ignore = true
    }
  }, [configName, detailsOpen, suiteId])

  return { configDetails, configLoading, configError, setConfigError }
}

const parseSuiteContextFile = (file?: SuiteContextFile | null) => {
  if (!file) return null
  try {
    const content = yaml.load(file.content) as Record<string, unknown> | undefined
    return {
      filename: file.filename,
      content: content ?? {},
    }
  } catch (error) {
    console.error('Failed to parse YAML from suite context', error)
    return {
      filename: file.filename,
      content: {},
    }
  }
}

const convertSuiteContext = (
  context: SuiteContextResponse,
): ExperimentConfigDetailsResponse | null => {
  if (!context.experiments.length) {
    return null
  }

  const entries = context.experiments.map((experiment) => ({
    id: experiment.id,
    name: experiment.name,
    environment: parseSuiteContextFile(experiment.environment),
    controller: parseSuiteContextFile(experiment.controller),
    environment_path: experiment.environment?.original_path ?? null,
    controller_path: experiment.controller?.original_path ?? null,
  }))

  const first = context.experiments[0]

  return {
    experiment: parseSuiteContextFile(first.experiment) ?? {
      filename: first.experiment.filename,
      content: {},
    },
    environment: parseSuiteContextFile(first.environment) ?? undefined,
    controller: parseSuiteContextFile(first.controller) ?? undefined,
    experiments: entries,
  }
}
