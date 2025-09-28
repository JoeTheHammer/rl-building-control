import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Loader2 } from 'lucide-react'
import {
  fetchExperimentConfigs,
  normalizeExperimentFilename,
  saveExperimentConfig,
  stripExperimentExtension,
} from '@/services/experiment-service.ts'
import {
  toExperimentDefinitions,
  type ExperimentFormState,
} from '@/services/yaml-service.ts'

interface ExperimentSaveDialogProps {
  open: boolean
  onClose: () => void
  experiments: ExperimentFormState[]
  onSaved: (filename: string) => void
  initialFilename?: string | null
}

const ExperimentSaveDialog = ({
  open,
  onClose,
  experiments,
  onSaved,
  initialFilename,
}: ExperimentSaveDialogProps) => {
  const [filename, setFilename] = useState('')
  const [existingFiles, setExistingFiles] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [overwritePrompt, setOverwritePrompt] = useState(false)

  useEffect(() => {
    if (!open) {
      setFilename('')
      setExistingFiles([])
      setOverwritePrompt(false)
      setSaving(false)
      return
    }

    setLoading(true)
    const initialValue = initialFilename ?? ''
    setFilename(initialValue)

    fetchExperimentConfigs()
      .then(setExistingFiles)
      .catch((error) => {
        console.error('Failed to load experiment configs', error)
        toast.error('Unable to load existing experiment configs')
      })
      .finally(() => setLoading(false))
  }, [open, initialFilename])

  const normalizedExisting = useMemo(
    () =>
      new Set(
        existingFiles.map((file) =>
          normalizeExperimentFilename(stripExperimentExtension(file)),
        ),
      ),
    [existingFiles],
  )

  const handleClose = () => {
    if (saving) return
    onClose()
  }

  const handleSave = async () => {
    const trimmed = filename.trim()

    if (trimmed === '') {
      toast.error('Please provide a filename for the experiment configuration')
      return
    }

    if (experiments.length === 0) {
      toast.error('Add at least one experiment before saving')
      return
    }

    const normalizedInput = normalizeExperimentFilename(
      stripExperimentExtension(trimmed),
    )

    const fileExists = normalizedExisting.has(normalizedInput)

    if (fileExists && !overwritePrompt) {
      setOverwritePrompt(true)
      return
    }

    const finalFilename = `${stripExperimentExtension(trimmed)}.yaml`
    const payload = toExperimentDefinitions(experiments)

    setSaving(true)

    try {
      await saveExperimentConfig({
        filename: finalFilename,
        experiments: payload,
      })
      toast.success(`Experiment configuration saved as ${finalFilename}`)
      onSaved(finalFilename)
      onClose()
    } catch (error) {
      console.error('Failed to save experiment configuration', error)
      toast.error('Failed to save experiment configuration')
    } finally {
      setSaving(false)
      setOverwritePrompt(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent aria-describedby={undefined}>
        <DialogHeader>
          <DialogTitle>Save Experiment Configuration</DialogTitle>
          <DialogDescription>
            {overwritePrompt
              ? 'A configuration with this name already exists. Confirm to overwrite it.'
              : 'Enter a name for the experiment configuration.'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <Input
            autoFocus
            value={filename}
            onChange={(event) => {
              setFilename(event.target.value)
              setOverwritePrompt(false)
            }}
            placeholder="experiment-config"
            disabled={loading || saving}
          />
          {loading && (
            <p className="text-sm text-muted-foreground">
              Loading existing configurations...
            </p>
          )}
        </div>
        <DialogFooter className="mt-4 flex w-full justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={saving}
          >
            Cancel
          </Button>
          <Button type="button" onClick={handleSave} disabled={saving || loading}>
            {saving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : overwritePrompt ? (
              'Confirm Overwrite'
            ) : (
              'Save'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default ExperimentSaveDialog
