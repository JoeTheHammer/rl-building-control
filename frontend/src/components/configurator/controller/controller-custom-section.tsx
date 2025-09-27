import StringValueList from '../../shared/string-value-list.tsx'
import { Input } from '../../ui/input.tsx'

interface CustomSectionProps {
  modulePath: string
  className: string
  initArguments: string[]
  onModuleChange: (value: string) => void
  onClassNameChange: (value: string) => void
  onInitArgumentsChange: (values: string[]) => void
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
          <label className="text-sm font-semibold text-primary" htmlFor="custom-module">
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
          <label className="text-sm font-semibold text-primary" htmlFor="custom-class-name">
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
          <p className="text-muted-foreground text-sm">
            Provide key-value pairs using the format <code>key: value</code> or <code>key=value</code>.
            These will be converted into the <code>args</code> mapping inside the YAML configuration.
          </p>
        </div>
        <StringValueList
          values={initArguments}
          onChange={onInitArgumentsChange}
          emptyValueLabel="Argument"
        />
      </section>
    </div>
  )
}

export default CustomSection
