import React from 'react'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog.tsx'
import { Button } from '@/components/ui/button.tsx'
import { Checkbox } from '@/components/ui/checkbox.tsx'

interface CsvOption {
  id: string
  label: string
}

interface CsvExportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  options: CsvOption[]
  selected: string[]
  onToggle: (optionId: string) => void
  onExport: () => void
}

const CsvExportDialog: React.FC<CsvExportDialogProps> = ({
  open,
  onOpenChange,
  options,
  selected,
  onToggle,
  onExport,
}) => {
  const isOptionSelected = (id: string) => selected.includes(id)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl" aria-describedby={undefined}>
        <DialogHeader>
          <DialogTitle>Export Data to CSV</DialogTitle>
          <DialogDescription>
            Pick one or more data series that should be included in the exported
            CSV file.
          </DialogDescription>
        </DialogHeader>

        {options.length === 0 ? (
          <div className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
            No exportable data series available for the current selection.
          </div>
        ) : (
          <div className="max-h-80 space-y-3 overflow-y-auto pr-2">
            {options.map((option) => (
              <label
                key={option.id}
                className="flex cursor-pointer items-start gap-3 rounded-lg border border-transparent p-2 transition hover:border-accent"
              >
                <Checkbox
                  checked={isOptionSelected(option.id)}
                  onCheckedChange={() => onToggle(option.id)}
                  className="mt-1"
                />
                <span className="text-sm leading-tight">{option.label}</span>
              </label>
            ))}
          </div>
        )}

        <DialogFooter className="flex flex-col gap-2 sm:flex-row sm:justify-between">
          <span className="text-xs text-muted-foreground">
            {selected.length} dataset{selected.length === 1 ? '' : 's'} selected
          </span>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button onClick={onExport} disabled={selected.length === 0}>
              Download CSV
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export type { CsvOption }
export default CsvExportDialog
