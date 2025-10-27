import { Info, Plus, Trash2 } from 'lucide-react'
import KeyValueList, { type KeyValue } from '../../shared/key-value-list.tsx'
import StringValueList from '../../shared/string-value-list.tsx'
import { Button } from '../../ui/button.tsx'
import { Input } from '../../ui/input.tsx'
import type { ControllerRule } from './controller-types.ts'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../../ui/tooltip.tsx'

interface RuleBasedSectionProps {
  customVariables: KeyValue[]
  onCustomVariablesChange: (values: KeyValue[]) => void
  stateSpace: string[]
  onStateSpaceChange: (values: string[]) => void
  rules: ControllerRule[]
  onRuleChange: (
    index: number,
    field: keyof ControllerRule,
    value: string,
  ) => void
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
    <div className="flex flex-col gap-5">
      <section className="grid gap-6 lg:grid-cols-2">
        {/* ----------------------- Custom Variables ----------------------- */}
        <div className="flex flex-col gap-2">
          <div>
            <h2 className="text-primary text-lg font-semibold">
              Custom Variables
            </h2>
          </div>
          <KeyValueList
            values={customVariables}
            onChange={onCustomVariablesChange}
            emptyKeyLabel="Variable"
            emptyValueLabel="Value"
          />
        </div>

        {/* ----------------------- State Space ----------------------- */}
        <div className="flex flex-col gap-2">
          <div className="flex flex-row items-center gap-2">
            <h2 className="text-primary text-lg font-semibold">State Space</h2>

            {/* ✅ Tooltip for Info icon */}
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Info className="text-primary h-5 w-5 cursor-pointer" />
                </TooltipTrigger>
                <TooltipContent className="text-md max-w-sm">
                  <p>
                    Can be empty for Sinergym environments as for them, the
                    state space is determined automatically in the testbed.
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <h5 className="text-primary text-lg font-extralight">
              (For Sinergym env optional)
            </h5>
          </div>

          <StringValueList
            values={stateSpace}
            onChange={onStateSpaceChange}
            emptyValueLabel="State variable"
          />
        </div>
      </section>

      {/* ----------------------- Rules Section ----------------------- */}
      <section className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-primary text-lg font-semibold">Rules</h2>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          {rules.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              No rules defined yet.
            </p>
          ) : (
            rules.map((rule, index) => (
              <div
                key={`rule-${index}`}
                className="grid gap-4 rounded-md border p-4 lg:grid-cols-[1fr_auto]"
              >
                <div className="grid gap-4 md:grid-cols-[auto_auto_100px]">
                  <div className="flex flex-col gap-2">
                    <label
                      className="text-primary text-sm font-semibold"
                      htmlFor={`rule-condition-${index}`}
                    >
                      Condition
                    </label>
                    <Input
                      id={`rule-condition-${index}`}
                      value={rule.condition}
                      onChange={(event) =>
                        onRuleChange(index, 'condition', event.target.value)
                      }
                      placeholder="Enter condition"
                    />
                  </div>
                  <div className="flex flex-col gap-2">
                    <label
                      className="text-primary text-sm font-semibold"
                      htmlFor={`rule-action-${index}`}
                    >
                      Action
                    </label>
                    <Input
                      id={`rule-action-${index}`}
                      value={rule.action}
                      onChange={(event) =>
                        onRuleChange(index, 'action', event.target.value)
                      }
                      placeholder="Enter action"
                    />
                  </div>
                  <div className="flex w-full justify-end-safe pt-7">
                    <Button type="button" onClick={() => onRemoveRule(index)}>
                      <Trash2 className="mr-2 h-4 w-4" /> Remove
                    </Button>
                  </div>
                </div>
              </div>
            ))
          )}
          <Button type="button" className="w-[200px]" onClick={onAddRule}>
            <Plus className="mr-2 h-4 w-4" /> Add rule
          </Button>
        </div>
      </section>
    </div>
  )
}

export default RuleBasedSection
