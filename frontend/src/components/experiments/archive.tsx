import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { ChartNoAxesCombined, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { useNavigate } from 'react-router-dom'

import CustomPage from '@/components/shared/page.tsx'
import SuiteCard from '@/components/experiments/suite-card/suite-card.tsx'
import { Button } from '@/components/ui/button.tsx'
import { Input } from '@/components/ui/input.tsx'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog.tsx'
import {
  deleteExperimentSuite,
  fetchExperimentSuites,
  type ExperimentSuiteApiResponse,
  type TensorBoardStatusResponse,
} from '@/services/experiment-service.ts'

const Archive = () => {
  const navigate = useNavigate()
  const [suites, setSuites] = useState<ExperimentSuiteApiResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [suitePendingDeletion, setSuitePendingDeletion] =
    useState<ExperimentSuiteApiResponse | null>(null)
  const [deleting, setDeleting] = useState(false)

  const handleShowResults = useCallback(
    (suiteId: number) => {
      navigate(`/data-analytics?suiteId=${suiteId}`, {
        state: { suiteId },
      })
    },
    [navigate],
  )

  const handleDeleteDialogClose = useCallback(() => {
    if (!deleting) {
      setSuitePendingDeletion(null)
    }
  }, [deleting, setSuitePendingDeletion])

  const handleDeleteSuite = useCallback(async () => {
    if (!suitePendingDeletion) {
      return
    }

    const targetSuite = suitePendingDeletion
    setDeleting(true)
    try {
      await deleteExperimentSuite(targetSuite.id)
      setSuites((prev) => prev.filter((item) => item.id !== targetSuite.id))
      toast.success(`Deleted "${targetSuite.name}"`)
      setSuitePendingDeletion(null)
    } catch (err) {
      console.error('Failed to delete experiment suite', err)
      toast.error('Failed to delete experiment suite')
    } finally {
      setDeleting(false)
    }
  }, [setSuites, suitePendingDeletion])

  const handleTensorboardStatusChange = useCallback(
    (suiteId: number, status: TensorBoardStatusResponse) => {
      setSuites((prev) =>
        prev.map((suite) =>
          suite.id === suiteId
            ? {
                ...suite,
                tensorboard: status,
                tensorboard_enabled: status.enabled,
              }
            : suite,
        ),
      )
    },
    [],
  )

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

  const filteredSuites = useMemo(() => {
    const query = searchQuery.trim().toLowerCase()
    if (!query) {
      return archivedSuites
    }

    return archivedSuites.filter((suite) => {
      const searchableValues = [suite.name, suite.path, suite.config_filename]
      return searchableValues
        .filter((value): value is string => Boolean(value))
        .some((value) => value.toLowerCase().includes(query))
    })
  }, [archivedSuites, searchQuery])

  return (
    <CustomPage>
      <div className="flex flex-col gap-6 pt-4">
        <Section
          title="Archived Experiment Suites"
          actions={
            <Input
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search by name, path, or file..."
              className="w-full sm:max-w-xs"
            />
          }
        >
          {loading ? (
            <EmptyState message="Loading archived experiment suites..." />
          ) : error ? (
            <EmptyState message={error} />
          ) : filteredSuites.length === 0 ? (
            <EmptyState
              message={
                searchQuery.trim()
                  ? 'No archived experiment suites match your search.'
                  : 'No archived experiment suites.'
              }
            />
          ) : (
            filteredSuites.map((suite) => (
              <SuiteCard
                key={suite.id}
                suite={suite}
                status={suite.status}
                idLabel={`ID: ${suite.id}`}
                actions={
                  <div className="flex flex-col gap-2 sm:flex-row">
                    <Button onClick={() => handleShowResults(suite.id)}>
                      <div className="flex gap-2">
                        <ChartNoAxesCombined className="size-4" /> Show Results
                      </div>
                    </Button>
                    <Button onClick={() => setSuitePendingDeletion(suite)}>
                      <div className="flex gap-2">
                        <Trash2 className="size-4" /> Delete
                      </div>
                    </Button>
                  </div>
                }
                onTensorboardStatusChange={(status) =>
                  handleTensorboardStatusChange(suite.id, status)
                }
              />
            ))
          )}
        </Section>
        <Dialog
          open={suitePendingDeletion !== null}
          onOpenChange={(open) => {
            if (!open) {
              handleDeleteDialogClose()
            }
          }}
        >
          <DialogContent showCloseButton={!deleting}>
            <DialogHeader>
              <DialogTitle>Delete experiment data</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete this experiment suite? All data
                will be deleted.
              </DialogDescription>
            </DialogHeader>
            <span className="text-sm font-bold">
              {'Folder: ' + suitePendingDeletion?.path + '/'}
            </span>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={handleDeleteDialogClose}
                disabled={deleting}
              >
                Cancel
              </Button>
              <Button
                disabled={deleting}
                onClick={() => {
                  void handleDeleteSuite()
                }}
              >
                {deleting ? 'Deleting…' : 'Delete'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </CustomPage>
  )
}

const Section: React.FC<{
  title: string
  actions?: React.ReactNode
  children: React.ReactNode
}> = ({ title, actions, children }) => (
  <div className="border-primary/20 bg-background rounded-xl border p-6 shadow-sm">
    <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <h2 className="text-primary text-xl font-semibold">{title}</h2>
      {actions ? <div className="w-full sm:max-w-xs">{actions}</div> : null}
    </div>
    <div className="space-y-4">{children}</div>
  </div>
)

const EmptyState: React.FC<{ message: string }> = ({ message }) => (
  <div className="border-primary/30 text-muted-foreground rounded-lg border border-dashed px-4 py-6 text-center">
    {message}
  </div>
)

export default Archive
