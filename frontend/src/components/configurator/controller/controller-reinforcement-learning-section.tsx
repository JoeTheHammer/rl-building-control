import { Button } from '../../ui/button.tsx'
import { Checkbox } from '../../ui/checkbox.tsx'
import { Input } from '../../ui/input.tsx'
import KeyValueList, { type KeyValue } from '../../shared/key-value-list.tsx'
import { CONTROLLER_HYPERPARAMETER_SUGGESTIONS } from './controller-defaults.ts'
import type { ControllerSettings } from './controller-types.ts'

interface ReinforcementLearningSectionProps {
  settings: ControllerSettings
  onNumberChange: (
    field: 'trainingTimesteps' | 'numEpisodes' | 'numTrials',
    value: string,
  ) => void
  onBooleanChange: (
    field: 'reportTraining' | 'denormalize' | 'tensorboardLogs' | 'hpTuning',
    value: boolean,
  ) => void
  onHyperparametersChange: (values: KeyValue[]) => void
  onResetHyperparameters: () => void
}

const ReinforcementLearningSection = ({
  settings,
  onNumberChange,
  onBooleanChange,
  onHyperparametersChange,
  onResetHyperparameters,
}: ReinforcementLearningSectionProps) => {
  return (
    <div className="flex flex-col gap-8">
      <section className="grid gap-6 lg:grid-cols-2">
        <div className="flex flex-col gap-2">
          <label
            className="text-sm font-semibold text-primary"
            htmlFor="training-timesteps"
          >
            Training Timesteps
          </label>
          <Input
            id="training-timesteps"
            type="number"
            value={settings.trainingTimesteps ?? ''}
            onChange={(event) => onNumberChange('trainingTimesteps', event.target.value)}
            placeholder="Enter number"
          />
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="flex flex-col gap-3">
          <span className="text-primary text-sm font-semibold">Training Options</span>
          <label className="flex items-center gap-3 text-sm">
            <Checkbox
              checked={settings.reportTraining}
              onCheckedChange={(checked) => onBooleanChange('reportTraining', !!checked)}
            />
            <span>Report training</span>
          </label>
          <label className="flex items-center gap-3 text-sm">
            <Checkbox
              checked={settings.denormalize}
              onCheckedChange={(checked) => onBooleanChange('denormalize', !!checked)}
            />
            <span>Denormalize</span>
          </label>
          <label className="flex items-center gap-3 text-sm">
            <Checkbox
              checked={settings.tensorboardLogs}
              onCheckedChange={(checked) => onBooleanChange('tensorboardLogs', !!checked)}
            />
            <span>Tensorboard logs</span>
          </label>
        </div>

        <div className="flex flex-col gap-3">
          <label className="flex items-center gap-3 text-sm">
            <Checkbox
              checked={settings.hpTuning}
              onCheckedChange={(checked) => onBooleanChange('hpTuning', !!checked)}
            />
            <span className="text-primary text-sm font-semibold">HP tuning</span>
          </label>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="flex flex-col gap-2">
              <label className="text-sm font-semibold text-primary" htmlFor="num-episodes">
                Num episodes
              </label>
              <Input
                id="num-episodes"
                type="number"
                value={settings.numEpisodes ?? ''}
                onChange={(event) => onNumberChange('numEpisodes', event.target.value)}
                placeholder="Enter number"
                disabled={!settings.hpTuning}
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-sm font-semibold text-primary" htmlFor="num-trials">
                Num trials
              </label>
              <Input
                id="num-trials"
                type="number"
                value={settings.numTrials ?? ''}
                onChange={(event) => onNumberChange('numTrials', event.target.value)}
                placeholder="Enter number"
                disabled={!settings.hpTuning}
              />
            </div>
          </div>
        </div>
      </section>

      <section className="flex flex-col gap-4">
        <div>
          <h2 className="text-primary text-lg font-semibold">Hyperparameters</h2>
          <p className="text-muted-foreground text-sm">
            Prefilled with the most common settings across sample controller configurations.
            Adjust or remove any values as needed.
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            {CONTROLLER_HYPERPARAMETER_SUGGESTIONS.map((suggestion) => (
              <span key={suggestion.key} className="rounded-full border border-dashed px-3 py-1">
                <span className="font-semibold text-primary">{suggestion.key}</span>: {suggestion.value}
              </span>
            ))}
          </div>
        </div>
        <div className="flex flex-col gap-3">
          <KeyValueList
            values={settings.hyperparameters}
            onChange={onHyperparametersChange}
            emptyKeyLabel="Hyperparameter"
            emptyValueLabel="Value"
          />
          <Button type="button" variant="outline" className="w-fit" onClick={onResetHyperparameters}>
            Reset to suggestions
          </Button>
        </div>
      </section>
    </div>
  )
}

export default ReinforcementLearningSection
