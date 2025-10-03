import React, { useMemo } from 'react'
import yaml from 'js-yaml'

import CustomEditor from '@/components/shared/custom-editor.tsx'
import { Button } from '@/components/ui/button.tsx'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import type { ConfigDetailsSection } from '@/services/experiment-service.ts'

interface ConfigSectionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  section: ConfigDetailsSection | null | undefined
  loading: boolean
  error?: string | null
  onEdit?: () => void
  editable?: boolean
}

const serializeSection = (
  section: ConfigDetailsSection | null | undefined,
): string => {
  if (!section) return ''
  try {
    return yaml.dump(section.content ?? {}, { noRefs: true })
  } catch (error) {
    console.error('Failed to serialize config section', error)
    return JSON.stringify(section.content ?? {}, null, 2)
  }
}

const ConfigSectionDialog: React.FC<ConfigSectionDialogProps> = ({
  open,
  onOpenChange,
  title,
  section,
  loading,
  error,
  onEdit,
  editable = true,
}) => {
  const content = useMemo(() => serializeSection(section), [section])

  const onClose = () => {
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-h-[85vh] max-w-5xl sm:max-w-5xl"
        aria-describedby={undefined}
      >
        <DialogHeader className="gap-1">
          <DialogTitle>{title} configuration</DialogTitle>
          {section?.filename ? (
            <DialogDescription className="text-xs sm:text-sm">
              File: {section.filename}
            </DialogDescription>
          ) : (
            <DialogDescription>
              Review the {title.toLowerCase()} settings associated with this
              suite.
            </DialogDescription>
          )}
        </DialogHeader>
        <div className="max-h-[60vh] overflow-y-auto pr-1">
          {loading ? (
            <p className="text-muted-foreground text-sm">
              Loading configuration…
            </p>
          ) : error ? (
            <p className="text-destructive text-sm">{error}</p>
          ) : section ? (
            <div className="border-muted/40 rounded-md border">
              <CustomEditor
                defaultLanguage="yaml"
                height="820px"
                value={content}
                options={{
                  readOnly: true,
                  minimap: { enabled: false },
                }}
              />
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">
              This section could not be loaded from the configuration files.
            </p>
          )}
        </div>
        {editable && onEdit && (
          <DialogFooter>
            <Button onClick={onEdit} disabled={!section}>
              Edit {title.toLowerCase()}
            </Button>
            <Button variant="outline" onClick={onClose} disabled={!section}>
              Close
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  )
}

export default ConfigSectionDialog
