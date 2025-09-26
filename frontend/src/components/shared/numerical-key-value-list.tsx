import { Plus, Trash2 } from 'lucide-react'
import { Input } from '../ui/input.tsx'
import { Button } from '../ui/button.tsx'

export interface NumericalKeyValue {
  key: string
  value: number
}

interface NumericalKeyValueListProps {
  values: NumericalKeyValue[]
  onChange: (values: NumericalKeyValue[]) => void
  emptyKeyLabel?: string
  emptyValueLabel?: string
}

const NumericalKeyValueList = ({
  values,
  onChange,
  emptyKeyLabel = 'Key',
  emptyValueLabel = 'Value',
}: NumericalKeyValueListProps) => {
  const handleAdd = () => {
    onChange([...values, { key: '', value: 0 }])
  }

  const handleChange = (
    index: number,
    field: keyof NumericalKeyValue,
    newValue: string,
  ) => {
    const updated = values.map((item, currentIndex) =>
      currentIndex === index
        ? {
            ...item,
            [field]: field === 'value' ? Number(newValue) || 0 : newValue,
          }
        : item,
    )
    onChange(updated)
  }

  const handleRemove = (index: number) => {
    onChange(values.filter((_, currentIndex) => currentIndex !== index))
  }

  return (
    <div className="flex flex-col gap-2">
      {values.map((item, index) => (
        <div key={`nkv-${index}`} className="flex items-center gap-2">
          {/* Key input */}
          <Input
            value={item.key}
            onChange={(e) => handleChange(index, 'key', e.target.value)}
            placeholder={`${emptyKeyLabel} ${index + 1}`}
            className="flex-1"
          />

          {/* Value input (number) */}
          <Input
            type="number"
            value={item.value}
            onChange={(e) => handleChange(index, 'value', e.target.value)}
            placeholder={`${emptyValueLabel} ${index + 1}`}
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

export default NumericalKeyValueList
