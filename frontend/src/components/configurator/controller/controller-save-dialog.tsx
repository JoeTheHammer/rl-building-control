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
  fetchControllerConfigs,
  normalizeControllerFilename,
  saveControllerConfig,
  stripControllerExtension,
  type SaveControllerPayload,
} from '@/services/controller-service'
import { toast } from 'sonner'

type ControllerConfigData = SaveControllerPayload['settings']

interface ControllerSaveDialogProps {
  open: boolean
  onClose: () => void
  initialFilename?: string | null
  settings: ControllerConfigData
  onSaved: (filename: string) => void
}

const ControllerSaveDialog = ({
  open,
  onClose,
  initialFilename,
  settings,
  onSaved,
}: ControllerSaveDialogProps) => {
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

    fetchControllerConfigs()
      .then(setExistingFiles)
      .catch((error) => {
        console.error('Failed to load controller configs', error)
        toast.error('Unable to load existing controller configs')
      })
      .finally(() => setLoading(false))
  }, [open, initialFilename])

  const normalizedExisting = useMemo(
    () =>
      new Set(
        existingFiles.map((file) =>
          normalizeControllerFilename(stripControllerExtension(file)),
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
      toast.error('Please provide a filename for the controller configuration')
      return
    }

    const normalizedInput = normalizeControllerFilename(
      stripControllerExtension(trimmed),
    )
    const fileExists = normalizedExisting.has(normalizedInput)

    if (fileExists && !overwritePrompt) {
      setOverwritePrompt(true)
      return
    }

    const finalFilename = `${stripControllerExtension(trimmed)}.yaml`

    setSaving(true)
    try {
      await saveControllerConfig({
        filename: finalFilename,
        settings,
      })
      toast.success(`Controller configuration saved as ${finalFilename}`)
      onSaved(finalFilename)
      onClose()
    } catch (error) {
      console.error('Failed to save controller configuration', error)
      toast.error('Failed to save controller configuration')
    } finally {
      setSaving(false)
      setOverwritePrompt(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent aria-describedby={undefined}>
        <DialogHeader>
          <DialogTitle>Save Controller Configuration</DialogTitle>
          <DialogDescription>
            {overwritePrompt
              ? 'A configuration with this name already exists. Confirm to overwrite it.'
              : 'Enter a name for the controller configuration.'}
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
            placeholder="controller-config"
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

export default ControllerSaveDialog
