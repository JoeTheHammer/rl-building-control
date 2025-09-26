import { Plus, Trash2 } from 'lucide-react'
import { Input } from '../ui/input.tsx'
import { Button } from '../ui/button.tsx'

interface NumericValueListProps {
  values: number[]
  onChange: (values: number[]) => void
}

const NumericValueList = ({ values, onChange }: NumericValueListProps) => {
  const handleAdd = () => {
    onChange([...values, 0])
  }

  const handleChange = (index: number, value: string) => {
    const numeric = parseFloat(value)
    const updated = values.map((v, i) =>
      i === index ? (isNaN(numeric) ? 0 : numeric) : v,
    )
    onChange(updated)
  }

  const handleRemove = (index: number) => {
    onChange(values.filter((_, i) => i !== index))
  }

  return (
    <div className="flex flex-col gap-2">
      {values.map((v, index) => (
        <div key={index} className="flex items-center gap-2">
          <Input
            type="number"
            value={v}
            onChange={(e) => handleChange(index, e.target.value)}
          />
          <Button size="icon" onClick={() => handleRemove(index)}>
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

export default NumericValueList
