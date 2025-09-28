import { useEffect, useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { fetchControllerConfigs } from '@/services/controller-service'

interface ControllerConfigDialogProps {
  open: boolean
  onClose: () => void
  onSelect: (name: string) => void
}

const ControllerConfigDialog = ({
  open,
  onClose,
  onSelect,
}: ControllerConfigDialogProps) => {
  const [configs, setConfigs] = useState<string[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (open) {
      setLoading(true)
      fetchControllerConfigs()
        .then(setConfigs)
        .finally(() => setLoading(false))
    }
  }, [open])

  const filtered = configs.filter((c) =>
    c.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent
        className="max-h-[66vh] max-w-lg overflow-hidden"
        aria-describedby={undefined}
      >
        <DialogHeader>
          <DialogTitle>Select Controller Configuration</DialogTitle>
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
          <div className="max-h-[50vh] space-y-2 overflow-y-auto pr-2">
            {filtered.map((c) => (
              <Button
                key={c}
                variant="ghost"
                className="w-full justify-start border"
                onClick={() => {
                  onSelect(c)
                  onClose()
                }}
              >
                {c}
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

export default ControllerConfigDialog
