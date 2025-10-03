import React from 'react'

import { Button } from '@/components/ui/button.tsx'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

interface CompletedLogDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  lines: string[]
  loading: boolean
  error?: string | null
  title?: string
}

const CompletedLogDialog: React.FC<CompletedLogDialogProps> = ({
  open,
  onOpenChange,
  lines,
  loading,
  error,
  title = 'Experiment logs',
}) => (
  <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent
      className="max-h-[85vh] max-w-4xl sm:max-w-5xl"
      aria-describedby={undefined}
    >
      <DialogHeader className="gap-1">
        <DialogTitle>{title}</DialogTitle>
        <DialogDescription>
          Review the captured log output for this experiment suite.
        </DialogDescription>
      </DialogHeader>
      <div className="border-muted/40 bg-muted/40 max-h-[60vh] overflow-hidden rounded-md border">
        <div className="max-h-[60vh] overflow-y-auto p-4">
          {loading ? (
            <p className="text-muted-foreground text-sm">Loading logs…</p>
          ) : error ? (
            <p className="text-destructive text-sm">{error}</p>
          ) : lines.length === 0 ? (
            <p className="text-muted-foreground text-sm">No logs were recorded.</p>
          ) : (
            <pre className="text-xs leading-relaxed text-muted-foreground whitespace-pre-wrap">
              {lines.join('\n')}
            </pre>
          )}
        </div>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={() => onOpenChange(false)}>
          Close
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
)

export default CompletedLogDialog
