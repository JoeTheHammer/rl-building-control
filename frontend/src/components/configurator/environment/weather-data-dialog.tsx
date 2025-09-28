import { useEffect, useState } from 'react'
import { fetchWeatherFolders } from '@/services/weather-service'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Folder } from 'lucide-react'

interface WeatherFolderDialogProps {
  open: boolean
  onClose: () => void
  onSelect: (folder: string) => void
}

const WeatherFolderDialog = ({
  open,
  onClose,
  onSelect,
}: WeatherFolderDialogProps) => {
  const [folders, setFolders] = useState<string[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (open) {
      setLoading(true)
      fetchWeatherFolders()
        .then(setFolders)
        .finally(() => setLoading(false))
    }
  }, [open])

  const filtered = folders.filter((f) =>
    f.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent
        className="max-h-[66vh] max-w-lg overflow-hidden"
        aria-describedby={undefined}
      >
        <DialogHeader>
          <DialogTitle>Select Weather Folder</DialogTitle>
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
            {filtered.map((f) => (
              <Button
                key={f}
                variant="ghost"
                className="w-full justify-start border"
                onClick={() => {
                  onSelect(f)
                  onClose()
                }}
              >
                <Folder className="mr-2 h-4 w-4" />
                {f}
              </Button>
            ))}
            {filtered.length === 0 && (
              <p className="text-muted-foreground">No folders found.</p>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

export default WeatherFolderDialog
