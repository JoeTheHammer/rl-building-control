// src/components/configurator/environment/BuildingModelDialog.tsx
import { useEffect, useState } from 'react'
import { fetchBuildingModels } from '@/services/building-service'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

interface BuildingModelDialogProps {
  open: boolean
  onClose: () => void
  onSelect: (file: string) => void
}

const BuildingModelDialog = ({
  open,
  onClose,
  onSelect,
}: BuildingModelDialogProps) => {
  const [models, setModels] = useState<string[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (open) {
      setLoading(true)
      fetchBuildingModels()
        .then(setModels)
        .finally(() => setLoading(false))
    }
  }, [open])

  const filteredModels = models.filter((m) =>
    m.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent
        className="max-h-[80vh] max-w-lg overflow-y-auto"
        aria-describedby={undefined}
      >
        <DialogHeader>
          <DialogTitle>Select Building Model</DialogTitle>
        </DialogHeader>
        <Input
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="mb-4"
        />
        {loading ? (
          <div>Loading...</div>
        ) : (
          <div className="h-full space-y-2 overflow-y-auto">
            {filteredModels.map((m) => (
              <Button
                key={m}
                variant="ghost"
                className="w-full justify-start border"
                onClick={() => {
                  onSelect(m)
                  onClose()
                }}
              >
                {m}
              </Button>
            ))}
            {filteredModels.length === 0 && (
              <p className="text-muted-foreground">No models found.</p>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

export default BuildingModelDialog
