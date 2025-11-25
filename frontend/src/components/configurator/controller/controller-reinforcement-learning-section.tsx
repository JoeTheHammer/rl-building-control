import { Checkbox } from '../../ui/checkbox.tsx'
import { Input } from '../../ui/input.tsx'
import NestedKeyValueList, { type KeyValue } from '@/components/shared/nested-key-value-list.tsx'
import type { ControllerSettings } from './controller-types.ts'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../ui/select.tsx'
import {
  HYPERPARAMETER_SAMPLERS,
  type HyperparameterSampler,
} from '@/constants/hyperparameter-samplers.ts'

interface ReinforcementLearningSectionProps {
  settings: ControllerSettings
  onNumberChange: (
    field:
      | 'trainingTimesteps'
      | 'hpTrainingTimesteps'
      | 'numEpisodes'
      | 'numTrials',
    value: string,
  ) => void
  onBooleanChange: (
    field: 'reportTraining' | 'denormalize' | 'tensorboardLogs' | 'hpTuning',
    value: boolean,
  ) => void
  onEnvironmentWrapperChange: (
    field: keyof ControllerSettings['environmentWrapper'],
    value: boolean,
  ) => void
  onHyperparametersChange: (values: KeyValue[]) => void
  onSamplerChange: (value: HyperparameterSampler) => void
}

const ReinforcementLearningSection = ({
  settings,
  onNumberChange,
  onBooleanChange,
  onEnvironmentWrapperChange,
  onHyperparametersChange,
  onSamplerChange,
}: ReinforcementLearningSectionProps) => {
  return (
    <div className="flex flex-col gap-6">
      {/* Row 1: Timesteps + HP tuning section */}
      <section className="grid items-end gap-6 lg:grid-cols-2">
        {/* Training timesteps (left side) */}
        <div className="flex flex-col gap-1">
          <label
            className="text-primary text-sm font-semibold"
            htmlFor="training-timesteps"
          >
            Total Training Timesteps
          </label>
          <Input
            id="training-timesteps"
            type="number"
            value={settings.trainingTimesteps ?? ''}
            onChange={(event) =>
              onNumberChange('trainingTimesteps', event.target.value)
            }
            placeholder="Enter number"
          />
        </div>

        {/* HP tuning + episodes/trials (right side) */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <Checkbox
              checked={settings.hpTuning}
              onCheckedChange={(checked) =>
                onBooleanChange('hpTuning', !!checked)
              }
            />
            <span className="text-primary text-sm font-semibold">
              Activate Hyperparameter tuning
            </span>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <div className="flex flex-col gap-1">
              <label
                className="text-primary text-sm font-semibold"
                htmlFor="num-episodes"
              >
                Num episodes
              </label>
              <Input
                id="num-episodes"
                type="number"
                value={settings.numEpisodes ?? ''}
                onChange={(event) =>
                  onNumberChange('numEpisodes', event.target.value)
                }
                placeholder="Enter"
                disabled={!settings.hpTuning}
              />
            </div>

            <div className="flex flex-col gap-1">
              <label
                className="text-primary text-sm font-semibold"
                htmlFor="num-trials"
              >
                Num trials
              </label>
              <Input
                id="num-trials"
                type="number"
                value={settings.numTrials ?? ''}
                onChange={(event) =>
                  onNumberChange('numTrials', event.target.value)
                }
                placeholder="Enter"
                disabled={!settings.hpTuning}
              />
            </div>

            <div className="flex flex-col gap-1">
              <label
                className="text-primary text-sm font-semibold"
                htmlFor="hp-sampler"
              >
                Sampler
              </label>
              <Select
                value={settings.hpSampler}
                onValueChange={(value) =>
                  onSamplerChange(value as HyperparameterSampler)
                }
                disabled={!settings.hpTuning}
              >
                <SelectTrigger
                  id="hp-sampler"
                  className="w-full"
                  disabled={!settings.hpTuning}
                >
                  <SelectValue placeholder="Select sampler" />
                </SelectTrigger>
                <SelectContent>
                  {HYPERPARAMETER_SAMPLERS.map((sampler) => (
                    <SelectItem key={sampler} value={sampler}>
                      {sampler.toUpperCase()}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-col gap-1">
              <label
                className="text-primary text-sm font-semibold"
                htmlFor="hp-training-timesteps"
              >
                Training timesteps
              </label>
              <Input
                id="hp-training-timesteps"
                type="number"
                value={settings.hpTrainingTimesteps ?? ''}
                onChange={(event) =>
                  onNumberChange('hpTrainingTimesteps', event.target.value)
                }
                placeholder="Enter"
                disabled={!settings.hpTuning}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Row 2: Training options inline */}
      <section className="flex flex-col gap-2">
        <span className="text-primary text-sm font-semibold">
          Training Options
        </span>
        <div className="flex flex-wrap gap-6 text-sm">
          <label className="flex items-center gap-2">
            <Checkbox
              checked={settings.reportTraining}
              onCheckedChange={(checked) =>
                onBooleanChange('reportTraining', !!checked)
              }
            />
            Report training
          </label>
          <label className="flex items-center gap-2">
            <Checkbox
              checked={settings.denormalize}
              onCheckedChange={(checked) =>
                onBooleanChange('denormalize', !!checked)
              }
            />
            Denormalize
          </label>
          <label className="flex items-center gap-2">
            <Checkbox
              checked={settings.tensorboardLogs}
              onCheckedChange={(checked) =>
                onBooleanChange('tensorboardLogs', !!checked)
              }
            />
            Tensorboard logs
          </label>
        </div>
      </section>

      {/* Row 3: Environment wrapper options */}
      <section className="flex flex-col gap-2">
        <span className="text-primary text-sm font-semibold">
          Environment Wrapper
        </span>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          <label className="flex items-center gap-2 text-sm">
            <Checkbox
              checked={settings.environmentWrapper.normalizeState}
              onCheckedChange={(checked) =>
                onEnvironmentWrapperChange('normalizeState', !!checked)
              }
            />
            Normalize state
          </label>
          <label className="flex items-center gap-2 text-sm">
            <Checkbox
              checked={settings.environmentWrapper.normalizeReward}
              onCheckedChange={(checked) =>
                onEnvironmentWrapperChange('normalizeReward', !!checked)
              }
            />
            Normalize reward
          </label>
          <label className="flex items-center gap-2 text-sm">
            <Checkbox
              checked={settings.environmentWrapper.normalizeAction}
              onCheckedChange={(checked) =>
                onEnvironmentWrapperChange('normalizeAction', !!checked)
              }
            />
            Normalize action
          </label>
          <label className="flex items-center gap-2 text-sm">
            <Checkbox
              checked={settings.environmentWrapper.continuousAction}
              onCheckedChange={(checked) =>
                onEnvironmentWrapperChange('continuousAction', !!checked)
              }
            />
            Continuous action
          </label>
          <label className="flex items-center gap-2 text-sm">
            <Checkbox
              checked={settings.environmentWrapper.discreteAction}
              onCheckedChange={(checked) =>
                onEnvironmentWrapperChange('discreteAction', !!checked)
              }
            />
            Discrete action
          </label>
        </div>
      </section>

      {/* Row 4: Hyperparameters */}
      <section className="flex flex-col gap-2">
        <h2 className="text-primary text-base font-semibold">
          Hyperparameters
        </h2>
        <NestedKeyValueList
          values={settings.hyperparameters}
          onChange={onHyperparametersChange}
          emptyKeyLabel="Hyperparameter"
          emptyValueLabel="Value"
        />
      </section>
    </div>
  )
}

export default ReinforcementLearningSection
