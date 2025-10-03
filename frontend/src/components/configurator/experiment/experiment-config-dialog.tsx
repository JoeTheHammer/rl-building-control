import { useEffect, useState } from 'react'

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { fetchExperimentConfigs } from '@/services/experiment-service.ts'

interface ExperimentConfigDialogProps {
  open: boolean
  onClose: () => void
  onSelect: (fullPath: string, fileName: string) => void
}

interface ConfigEntry {
  file: string
  fullPath: string
}

const ExperimentConfigDialog = ({
  open,
  onClose,
  onSelect,
}: ExperimentConfigDialogProps) => {
  const [configs, setConfigs] = useState<ConfigEntry[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!open) return

    setLoading(true)
    fetchExperimentConfigs()
      .then(({ files, fullPaths }) => {
        // pair files + fullPaths by index
        const entries = files.map((file, idx) => ({
          file,
          fullPath: fullPaths[idx],
        }))
        setConfigs(entries)
      })
      .finally(() => setLoading(false))
  }, [open])

  const filtered = configs.filter((config) =>
    config.file.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent
        className="max-h-[66vh] max-w-lg overflow-hidden"
        aria-describedby={undefined}
      >
        <DialogHeader>
          <DialogTitle>Select Experiment Configuration</DialogTitle>
        </DialogHeader>
        <Input
          placeholder="Search..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="mb-4"
        />
        {loading ? (
          <div>Loading...</div>
        ) : (
          <div className="max-h-[50vh] space-y-2 overflow-y-auto pr-2">
            {filtered.map((config) => (
              <Button
                key={config.fullPath}
                variant="ghost"
                className="w-full justify-start border"
                onClick={() => {
                  onSelect(config.fullPath, config.file) // return both
                  onClose()
                }}
              >
                {config.file}
              </Button>
            ))}
            {filtered.length === 0 && (
              <p className="text-muted-foreground">No configs found.</p>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

export default ExperimentConfigDialog
