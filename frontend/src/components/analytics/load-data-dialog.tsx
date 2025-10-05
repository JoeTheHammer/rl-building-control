import React from 'react'
import { Database } from 'lucide-react'

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog.tsx'
import { Button } from '@/components/ui/button.tsx'
import type { AnalyticsSuiteSummary } from '@/services/analytics-service.ts'

interface LoadDataDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  suites: AnalyticsSuiteSummary[]
  loading: boolean
  onRefresh: () => void
  onSelectSuite: (suiteId: number) => void
}

const LoadDataDialog: React.FC<LoadDataDialogProps> = ({
  open,
  onOpenChange,
  suites,
  loading,
  onRefresh,
  onSelectSuite,
}) => {
  const handleSelect = (suiteId: number) => {
    if (!loading) {
      onSelectSuite(suiteId)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Select Experiment Suite</DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Choose an experiment suite to load the exported analytics data.
            </p>
            <Button variant="outline" size="sm" onClick={onRefresh} disabled={loading}>
              Refresh
            </Button>
          </div>

          {loading && (
            <div className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
              Fetching available experiment suites...
            </div>
          )}

          {!loading && suites.length === 0 && (
            <div className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
              No experiment suites with exported analytics data were found.
            </div>
          )}

          {!loading && suites.length > 0 && (
            <div className="grid gap-3 md:grid-cols-2">
              {suites.map((suite) => (
                <button
                  key={suite.id}
                  type="button"
                  onClick={() => handleSelect(suite.id)}
                  disabled={!suite.has_data || loading}
                  className="flex flex-col items-start gap-2 rounded-lg border bg-card p-4 text-left transition hover:border-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <div className="flex items-center gap-2 text-sm font-semibold">
                    <Database className="size-4" />
                    <span>
                      #{suite.id} &mdash; {suite.name}
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {suite.has_data
                      ? suite.file_name || 'Analytics export available'
                      : 'No analytics export detected'}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default LoadDataDialog
