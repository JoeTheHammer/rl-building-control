import { Plus, Trash2 } from 'lucide-react'
import KeyValueList, { type KeyValue } from '../../shared/key-value-list.tsx'
import StringValueList from '../../shared/string-value-list.tsx'
import { Button } from '../../ui/button.tsx'
import { Input } from '../../ui/input.tsx'
import type { ControllerRule } from './controller-types.ts'

interface RuleBasedSectionProps {
  customVariables: KeyValue[]
  onCustomVariablesChange: (values: KeyValue[]) => void
  stateSpace: string[]
  onStateSpaceChange: (values: string[]) => void
  rules: ControllerRule[]
  onRuleChange: (index: number, field: keyof ControllerRule, value: string) => void
  onAddRule: () => void
  onRemoveRule: (index: number) => void
}

const RuleBasedSection = ({
  customVariables,
  onCustomVariablesChange,
  stateSpace,
  onStateSpaceChange,
  rules,
  onRuleChange,
  onAddRule,
  onRemoveRule,
}: RuleBasedSectionProps) => {
  return (
    <div className="flex flex-col gap-10">
      <section className="grid gap-6 lg:grid-cols-2">
        <div className="flex flex-col gap-4">
          <div>
            <h2 className="text-primary text-lg font-semibold">Custom Variables</h2>
            <p className="text-muted-foreground text-sm">
              Define any helper variables used within your rules.
            </p>
          </div>
          <KeyValueList
            values={customVariables}
            onChange={onCustomVariablesChange}
            emptyKeyLabel="Variable"
            emptyValueLabel="Value"
          />
        </div>

        <div className="flex flex-col gap-4">
          <div>
            <h2 className="text-primary text-lg font-semibold">State Space</h2>
            <p className="text-muted-foreground text-sm">
              Select the environment variables referenced by your rules.
            </p>
          </div>
          <StringValueList
            values={stateSpace}
            onChange={onStateSpaceChange}
            emptyValueLabel="State variable"
          />
        </div>
      </section>

      <section className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-primary text-lg font-semibold">Rules</h2>
            <p className="text-muted-foreground text-sm">
              Provide a condition and action for each rule. Actions should map to environment actuators.
            </p>
          </div>
          <Button type="button" onClick={onAddRule}>
            <Plus className="mr-2 h-4 w-4" /> Add rule
          </Button>
        </div>

        <div className="flex flex-col gap-4">
          {rules.length === 0 ? (
            <p className="text-muted-foreground text-sm">No rules defined yet.</p>
          ) : (
            rules.map((rule, index) => (
              <div key={`rule-${index}`} className="grid gap-4 rounded-md border p-4 lg:grid-cols-[1fr_auto]">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="flex flex-col gap-2">
                    <label className="text-sm font-semibold text-primary" htmlFor={`rule-condition-${index}`}>
                      Condition
                    </label>
                    <Input
                      id={`rule-condition-${index}`}
                      value={rule.condition}
                      onChange={(event) => onRuleChange(index, 'condition', event.target.value)}
                      placeholder="Enter condition"
                    />
                  </div>
                  <div className="flex flex-col gap-2">
                    <label className="text-sm font-semibold text-primary" htmlFor={`rule-action-${index}`}>
                      Action
                    </label>
                    <Input
                      id={`rule-action-${index}`}
                      value={rule.action}
                      onChange={(event) => onRuleChange(index, 'action', event.target.value)}
                      placeholder="Enter action"
                    />
                  </div>
                </div>
                <div className="flex justify-end">
                  <Button
                    type="button"
                    variant="ghost"
                    className="text-destructive hover:text-destructive"
                    onClick={() => onRemoveRule(index)}
                  >
                    <Trash2 className="mr-2 h-4 w-4" /> Remove
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  )
}

export default RuleBasedSection
