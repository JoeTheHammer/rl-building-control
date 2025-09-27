import { Input } from '../../ui/input.tsx'
import KeyValueList, {
  type KeyValue,
} from '@/components/shared/key-value-list.tsx'

interface CustomSectionProps {
  modulePath: string
  className: string
  initArguments: KeyValue[]
  onModuleChange: (value: string) => void
  onClassNameChange: (value: string) => void
  onInitArgumentsChange: (values: KeyValue[]) => void
}

const CustomSection = ({
  modulePath,
  className,
  initArguments,
  onModuleChange,
  onClassNameChange,
  onInitArgumentsChange,
}: CustomSectionProps) => {
  return (
    <div className="flex flex-col gap-8">
      <section className="grid gap-6 lg:grid-cols-2">
        <div className="flex flex-col gap-2">
          <label
            className="text-primary text-sm font-semibold"
            htmlFor="custom-module"
          >
            Module
          </label>
          <Input
            id="custom-module"
            value={modulePath}
            onChange={(event) => onModuleChange(event.target.value)}
            placeholder="controllers.custom.my_custom_controller"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label
            className="text-primary text-sm font-semibold"
            htmlFor="custom-class-name"
          >
            Class name
          </label>
          <Input
            id="custom-class-name"
            value={className}
            onChange={(event) => onClassNameChange(event.target.value)}
            placeholder="MyCustomController"
          />
        </div>
      </section>

      <section className="flex flex-col gap-4">
        <div>
          <h2 className="text-primary text-lg font-semibold">Init arguments</h2>
        </div>
        <KeyValueList
          values={initArguments}
          onChange={onInitArgumentsChange}
          emptyValueLabel="Value"
        />
      </section>
    </div>
  )
}

export default CustomSection
