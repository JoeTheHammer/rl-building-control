import React, { useMemo } from 'react'
import yaml from 'js-yaml'

import CustomEditor from '@/components/shared/custom-editor.tsx'
import { Button } from '@/components/ui/button.tsx'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import type {
  ConfigDetailsSection,
  ExperimentConfigDetailsResponse,
} from '@/services/experiment-service.ts'

interface ConfigDetailsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  details: ExperimentConfigDetailsResponse | null
  loading: boolean
  error?: string | null
  onEdit: (section: 'experiment' | 'environment' | 'controller') => void
}

interface ConfigSectionProps {
  title: string
  section: ConfigDetailsSection | null | undefined
  onEdit: () => void
  editable?: boolean
}

const ConfigSection: React.FC<ConfigSectionProps> = ({
  title,
  section,
  onEdit,
  editable = true,
}) => {
  const content = useMemo(() => {
    if (!section) return ''
    try {
      return yaml.dump(section.content ?? {}, { noRefs: true })
    } catch (error) {
      console.error('Failed to serialize config section', error)
      return JSON.stringify(section.content ?? {}, null, 2)
    }
  }, [section])

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-primary text-base font-semibold">{title}</h3>
          {section?.filename && (
            <p className="text-muted-foreground text-xs">{section.filename}</p>
          )}
        </div>
        {editable && (
          <Button variant="outline" size="sm" onClick={onEdit} disabled={!section}>
            Edit
          </Button>
        )}
      </div>
      <div className="border-muted/40 rounded-md border">
        <CustomEditor
          defaultLanguage="yaml"
          height="250px"
          value={content}
          options={{ readOnly: true, minimap: { enabled: false } }}
        />
      </div>
      {!section && (
        <p className="text-muted-foreground text-sm">
          This section could not be loaded from the configuration files.
        </p>
      )}
    </div>
  )
}

const ConfigDetailsDialog: React.FC<ConfigDetailsDialogProps> = ({
  open,
  onOpenChange,
  details,
  loading,
  error,
  onEdit,
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl" aria-describedby={undefined}>
        <DialogHeader>
          <DialogTitle>Configuration details</DialogTitle>
          <DialogDescription>
            Review the experiment, environment, and controller settings associated with
            this suite.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-6 overflow-y-auto">
          {loading ? (
            <p className="text-muted-foreground text-sm">Loading configuration…</p>
          ) : error ? (
            <p className="text-destructive text-sm">{error}</p>
          ) : (
            <div className="space-y-6">
              <ConfigSection
                title="Experiment"
                section={details?.experiment}
                onEdit={() => onEdit('experiment')}
              />
              <div className="bg-border h-px w-full" />
              <ConfigSection
                title="Environment"
                section={details?.environment ?? null}
                onEdit={() => onEdit('environment')}
              />
              <div className="bg-border h-px w-full" />
              <ConfigSection
                title="Controller"
                section={details?.controller ?? null}
                onEdit={() => onEdit('controller')}
              />
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default ConfigDetailsDialog
