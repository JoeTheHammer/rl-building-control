import { Plus, Trash2 } from 'lucide-react'
import { Input } from '../ui/input.tsx'
import { Button } from '../ui/button.tsx'

export interface KeyValue {
  key: string
  value: string
}

interface KeyValueListProps {
  values: KeyValue[]
  onChange: (values: KeyValue[]) => void
  emptyKeyLabel?: string
  emptyValueLabel?: string
}

const KeyValueList = ({
  values,
  onChange,
  emptyKeyLabel = 'Key',
  emptyValueLabel = 'Value',
}: KeyValueListProps) => {
  const handleAdd = () => {
    onChange([...values, { key: '', value: '' }])
  }

  const handleChange = (
    index: number,
    field: keyof KeyValue,
    newValue: string,
  ) => {
    const updated = values.map((item, currentIndex) =>
      currentIndex === index ? { ...item, [field]: newValue } : item,
    )
    onChange(updated)
  }

  const handleRemove = (index: number) => {
    onChange(values.filter((_, currentIndex) => currentIndex !== index))
  }

  return (
    <div className="flex flex-col gap-2">
      {values.map((item, index) => (
        <div key={`kv-${index}`} className="flex items-center gap-2">
          {/* Key input */}
          <Input
            value={item.key}
            onChange={(e) => handleChange(index, 'key', e.target.value)}
            placeholder={emptyKeyLabel}
            className="flex-1"
          />

          {/* Value input */}
          <Input
            value={item.value}
            onChange={(e) => handleChange(index, 'value', e.target.value)}
            placeholder={emptyValueLabel}
            className="flex-1"
          />

          {/* Remove button */}
          <Button size="icon" type="button" onClick={() => handleRemove(index)}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ))}

      <Button onClick={handleAdd} type="button" className="w-fit">
        <Plus className="mr-2 h-4 w-4" />
        Add Parameter
      </Button>
    </div>
  )
}

export default KeyValueList
