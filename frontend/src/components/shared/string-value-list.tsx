import { Plus, Trash2 } from 'lucide-react'
import { Input } from '../ui/input.tsx'
import { Button } from '../ui/button.tsx'

interface StringValueListProps {
  values: string[]
  onChange: (values: string[]) => void
  emptyValueLabel?: string
}

const StringValueList = ({
  values,
  onChange,
  emptyValueLabel = 'New value',
}: StringValueListProps) => {
  const handleAdd = () => {
    onChange([...values, ''])
  }

  const handleChange = (index: number, value: string) => {
    const updated = values.map((current, currentIndex) =>
      currentIndex === index ? value : current,
    )
    onChange(updated)
  }

  const handleRemove = (index: number) => {
    onChange(values.filter((_, currentIndex) => currentIndex !== index))
  }

  return (
    <div className="flex flex-col gap-2">
      {values.map((value, index) => (
        <div key={`string-value-${index}`} className="flex items-center gap-2">
          <Input
            value={value}
            onChange={(event) => handleChange(index, event.target.value)}
            placeholder={`${emptyValueLabel} ${index + 1}`}
          />
          <Button size="icon" type="button" onClick={() => handleRemove(index)}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ))}
      <Button onClick={handleAdd} type="button" className="w-fit">
        <Plus className="mr-2 h-4 w-4" />
        Add Value
      </Button>
    </div>
  )
}

export default StringValueList
