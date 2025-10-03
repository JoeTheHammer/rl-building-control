import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { ChartNoAxesCombined } from 'lucide-react'

import CustomPage from '@/components/shared/page.tsx'
import SuiteCard from '@/components/experiments/suite-card/suite-card.tsx'
import { Button } from '@/components/ui/button.tsx'
import {
  fetchExperimentSuites,
  type ExperimentSuiteApiResponse,
} from '@/services/experiment-service.ts'

const Archive = () => {
  const [suites, setSuites] = useState<ExperimentSuiteApiResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refreshSuites = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetchExperimentSuites()
      setSuites(response)
    } catch (err) {
      console.error('Failed to load archived experiment suites', err)
      setError('Unable to load archived experiment suites')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshSuites()
  }, [refreshSuites])

  const archivedSuites = useMemo(
    () => suites.filter((suite) => suite.archived),
    [suites],
  )

  return (
    <CustomPage>
      <div className="flex flex-col gap-6 pt-4">
        <Section title="Completed Experiment Suites">
          {loading ? (
            <EmptyState message="Loading archived experiment suites..." />
          ) : error ? (
            <EmptyState message={error} />
          ) : archivedSuites.length === 0 ? (
            <EmptyState message="No archived experiment suites." />
          ) : (
            archivedSuites.map((suite) => (
              <SuiteCard
                key={suite.id}
                suite={suite}
                status={suite.status}
                idLabel={`ID: ${suite.id}`}
                actions={
                  <Button onClick={() => console.log('Handle show results')}>
                    <div className="flex gap-2">
                      <ChartNoAxesCombined className="size-4" /> Show Results
                    </div>
                  </Button>
                }
              />
            ))
          )}
        </Section>
      </div>
    </CustomPage>
  )
}

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({
  title,
  children,
}) => (
  <div className="border-primary/20 bg-background rounded-xl border p-6 shadow-sm">
    <h2 className="text-primary mb-4 text-xl font-semibold">{title}</h2>
    <div className="space-y-4">{children}</div>
  </div>
)

const EmptyState: React.FC<{ message: string }> = ({ message }) => (
  <div className="border-primary/30 text-muted-foreground rounded-lg border border-dashed px-4 py-6 text-center">
    {message}
  </div>
)

export default Archive
