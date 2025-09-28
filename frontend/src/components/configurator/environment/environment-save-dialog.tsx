import { useEffect, useMemo, useState } from 'react'
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
  fetchEnvironmentConfigs,
  normalizeEnvironmentFilename,
  saveEnvironmentConfig,
  stripEnvironmentExtension,
  type SaveEnvironmentPayload,
} from '@/services/environment-service'
import { toast } from 'sonner'

type EnvironmentConfigData = SaveEnvironmentPayload['config']

interface EnvironmentSaveDialogProps {
  open: boolean
  onClose: () => void
  initialFilename?: string | null
  config: EnvironmentConfigData
  onSaved: (filename: string) => void
}

const EnvironmentSaveDialog = ({
  open,
  onClose,
  initialFilename,
  config,
  onSaved,
}: EnvironmentSaveDialogProps) => {
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

    const value = initialFilename ?? ''
    setFilename(value)
    setLoading(true)

    fetchEnvironmentConfigs()
      .then(setExistingFiles)
      .catch((error) => {
        console.error('Failed to load environment configs', error)
        toast.error('Unable to load existing environment configs')
      })
      .finally(() => setLoading(false))
  }, [open, initialFilename])

  const normalizedExisting = useMemo(
    () =>
      new Set(
        existingFiles.map((file) =>
          normalizeEnvironmentFilename(stripEnvironmentExtension(file)),
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
      toast.error('Please provide a filename for the environment configuration')
      return
    }

    const normalizedInput = normalizeEnvironmentFilename(
      stripEnvironmentExtension(trimmed),
    )
    const fileExists = normalizedExisting.has(normalizedInput)

    if (fileExists && !overwritePrompt) {
      setOverwritePrompt(true)
      return
    }

    const finalFilename = `${stripEnvironmentExtension(trimmed)}.yaml`

    setSaving(true)
    try {
      await saveEnvironmentConfig({
        filename: finalFilename,
        config,
      })
      toast.success(`Environment configuration saved as ${finalFilename}`)
      onSaved(finalFilename)
      onClose()
    } catch (error) {
      console.error('Failed to save environment configuration', error)
      toast.error('Failed to save environment configuration')
    } finally {
      setSaving(false)
      setOverwritePrompt(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent aria-describedby={undefined}>
        <DialogHeader>
          <DialogTitle>Save Environment Configuration</DialogTitle>
          <DialogDescription>
            {overwritePrompt
              ? 'A configuration with this name already exists. Confirm to overwrite it.'
              : 'Enter a name for the environment configuration.'}
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
            placeholder="environment-config"
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

export default EnvironmentSaveDialog
