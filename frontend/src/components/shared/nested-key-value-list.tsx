import { Plus, Trash2, CornerDownRight } from 'lucide-react'
import { Input } from '../ui/input.tsx'
import { Button } from '../ui/button.tsx'
import { useState, useEffect } from 'react'

export interface KeyValue {
  key: string
  value: string
}

interface NestedKeyValueListProps {
  values: KeyValue[]
  onChange: (values: KeyValue[]) => void
  emptyKeyLabel?: string
  emptyValueLabel?: string
}

// --- Helper Functions ---

/**
 * Flattens a nested object into an array of KeyValue pairs with dot notation.
 * e.g., { a: { b: "c" } } => [{ key: "a.b", value: "c" }]
 */
const flatten = (obj: Record<string, any>, prefix = ''): KeyValue[] => {
  let result: KeyValue[] = []
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const newKey = prefix ? `${prefix}.${key}` : key
      const value = obj[key]
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        result = result.concat(flatten(value, newKey))
      } else {
        result.push({ key: newKey, value: String(value) })
      }
    }
  }
  return result
}

/**
 * Unflattens an array of KeyValue pairs with dot notation into a nested object.
 * e.g., [{ key: "a.b", value: "c" }] => { a: { b: "c" } }
 */
const unflatten = (values: KeyValue[]): Record<string, any> => {
  const result: Record<string, any> = {}
  for (const { key, value } of values) {
    const keys = key.split('.')
    let current = result
    for (let i = 0; i < keys.length - 1; i++) {
      const k = keys[i]
      if (typeof current[k] !== 'object' || current[k] === null) {
        current[k] = {}
      }
      current = current[k]
    }
    current[keys[keys.length - 1]] = value
  }
  return result
}

// --- Recursive Sub-Component ---

interface RecursiveListProps {
  data: Record<string, any>
  updateData: (newData: Record<string, any>) => void
  emptyKeyLabel?: string
  emptyValueLabel?: string
}

const RecursiveList = ({ data, updateData, emptyKeyLabel, emptyValueLabel }: RecursiveListProps) => {
  const [newItemKey, setNewItemKey] = useState('')

  const handleKeyChange = (oldKey: string, newKey: string) => {
    const newData = { ...data }
    newData[newKey] = newData[oldKey]
    delete newData[oldKey]
    updateData(newData)
  }

  const handleValueChange = (key: string, newValue: string) => {
    updateData({ ...data, [key]: newValue })
  }

  const handleRemove = (key: string) => {
    const newData = { ...data }
    delete newData[key]
    updateData(newData)
  }

  const handleAddItem = (isNested: boolean) => {
    if (!newItemKey || data[newItemKey] !== undefined) {
      // Prevent adding empty or duplicate keys
      return
    }
    const newValue = isNested ? {} : ''
    updateData({ ...data, [newItemKey]: newValue })
    setNewItemKey('') // Reset input
  }

  return (
    <div className="flex flex-col gap-2 pl-4 border-l-2 border-gray-200">
      {Object.entries(data).map(([key, value]) => (
        <div key={key} className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <Input
              value={key}
              onChange={(e) => handleKeyChange(key, e.target.value)}
              placeholder={emptyKeyLabel}
              className="flex-1 font-mono text-sm"
            />

            {typeof value === 'object' && value !== null ? (
              <span className="flex-1 p-2 text-sm text-gray-500">Nested value</span>
            ) : (
              <Input
                value={value}
                onChange={(e) => handleValueChange(key, e.target.value)}
                placeholder={emptyValueLabel}
                className="flex-1"
              />
            )}

            <Button size="icon" type="button" onClick={() => handleRemove(key)}>
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>

          {typeof value === 'object' && value !== null && (
             <RecursiveList
                data={value}
                updateData={(newData) => updateData({ ...data, [key]: newData })}
                emptyKeyLabel={emptyKeyLabel}
                emptyValueLabel={emptyValueLabel}
             />
          )}
        </div>
      ))}

      {/* Add new item section */}
      <div className="flex items-center gap-2 mt-2">
         <Input
            value={newItemKey}
            onChange={(e) => setNewItemKey(e.target.value)}
            placeholder={emptyKeyLabel}
            className="flex-1"
          />
         <Button onClick={() => handleAddItem(false)} type="button" className="w-fit" size="sm">
            <Plus className="mr-2 h-4 w-4" />
            Add Value
          </Button>
          <Button onClick={() => handleAddItem(true)} type="button" className="w-fit" size="sm">
            <CornerDownRight className="mr-2 h-4 w-4" />
            Add Nested
          </Button>
      </div>
    </div>
  )
}


// --- Main Component ---

const NestedKeyValueList = ({
  values,
  onChange,
  emptyKeyLabel = 'Key',
  emptyValueLabel = 'Value',
}: NestedKeyValueListProps) => {
  const [nestedState, setNestedState] = useState<Record<string, any>>({})

  useEffect(() => {
    setNestedState(unflatten(values))
  }, [values])

  const handleUpdate = (newData: Record<string, any>) => {
    setNestedState(newData)
    onChange(flatten(newData))
  }

  return (
    <div className="flex flex-col gap-2">
        <RecursiveList
            data={nestedState}
            updateData={handleUpdate}
            emptyKeyLabel={emptyKeyLabel}
            emptyValueLabel={emptyValueLabel}
        />
    </div>
  )
}

export default NestedKeyValueList
