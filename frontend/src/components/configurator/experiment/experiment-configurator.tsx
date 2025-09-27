import { useState } from 'react'
import CustomPage from '../../shared/page.tsx'
import { Button } from '../../ui/button.tsx'
import { Input } from '../../ui/input.tsx'
import { Checkbox } from '../../ui/checkbox.tsx'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../ui/select.tsx'
import { Save, Code2, Monitor } from 'lucide-react'
import CustomEditor from '../../shared/custom-editor.tsx'

const ExperimentConfigurator = () => {
  const [controllerType, setControllerType] = useState('')
  const [numEpisodes, setNumEpisodes] = useState<number | undefined>(undefined)
  const [reporting, setReporting] = useState(false)
  const [reportingOptions, setReportingOptions] = useState({
    plots: false,
    denormalize: false,
    export: false,
  })

  const [devMode, setDevMode] = useState(false)
  const [editorValue, setEditorValue] = useState('')

  const handleSave = () => {
    if (devMode) {
      console.log('Saving from Dev Mode', editorValue)
    } else {
      console.log('Saving experiment configuration', {
        controllerType,
        numEpisodes,
        reporting,
        reportingOptions,
      })
    }
  }

  const handleToggleDevMode = () => {
    setDevMode((prev) => !prev)
  }

  return (
    <CustomPage>
      <div className="flex w-full flex-col gap-2 pt-2">
        {/* Top bar */}
        <div className="mb-2 grid grid-cols-4 items-center gap-2">
          <div className="col-span-2 col-start-1">
            <span className="text-primary text-md pt-2 font-bold md:text-xl">
              Experiment Configurator
            </span>
          </div>
          <div className="col-start-3 w-full">
            <Button
              onClick={handleToggleDevMode}
              type="button"
              variant={devMode ? 'default' : 'ghost'}
              className="text-md flex w-full gap-2 border"
            >
              {devMode ? (
                <>
                  <Monitor />
                  Switch to GUI Mode
                </>
              ) : (
                <>
                  <Code2 />
                  Switch to Dev Mode
                </>
              )}
            </Button>
          </div>

          <div className="col-start-4 w-full">
            <Button
              onClick={handleSave}
              type="button"
              className="text-md w-full cursor-pointer"
            >
              <div className="flex gap-2">
                <Save />
                <span>Save Configuration</span>
              </div>
            </Button>
          </div>
        </div>

        <hr className="border-t-primary w-full pb-2" />

        {devMode ? (
          <CustomEditor
            defaultLanguage="yaml"
            value={editorValue}
            onChange={(val) => setEditorValue(val ?? '')}
            height="600px"
          />
        ) : (
          <div className="flex flex-col gap-6 pt-4">
            {/* Grid section */}
            <div className="grid grid-cols-2 gap-6">
              {/* Environment */}
              <div className="flex flex-col gap-1">
                <label className="text-primary text-sm font-semibold">
                  Environment
                </label>
                <Button variant="outline">Choose environment</Button>
              </div>

              {/* Controller type */}
              <div className="flex flex-col gap-1">
                <label className="text-primary text-sm font-semibold">
                  Controller type
                </label>
                <Select
                  value={controllerType}
                  onValueChange={setControllerType}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select an option" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="rule">Rule Based</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                    <SelectItem value="ddpg">DDPG</SelectItem>
                    <SelectItem value="dqn">DQN</SelectItem>
                    <SelectItem value="ppo">PPO</SelectItem>
                    <SelectItem value="recurrent-ppo">Recurrent PPO</SelectItem>
                    <SelectItem value="sac">SAC</SelectItem>
                    <SelectItem value="td3">TD3</SelectItem>
                    <SelectItem value="a2c">A2C</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Controller */}
              <div className="flex flex-col gap-1">
                <label className="text-primary text-sm font-semibold">
                  Controller
                </label>
                <Button variant="outline">Choose controller</Button>
              </div>

              {/* Num episodes */}
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
                  value={numEpisodes ?? ''}
                  onChange={(e) => setNumEpisodes(Number(e.target.value))}
                  placeholder="Enter number"
                />
              </div>
            </div>

            {/* Reporting */}
            <div className="flex flex-col gap-2">
              <label className="text-primary flex items-center gap-2 text-sm font-semibold">
                <Checkbox
                  checked={reporting}
                  onCheckedChange={(checked) => setReporting(!!checked)}
                />
                Reporting
              </label>

              {reporting && (
                <div className="ml-6 flex flex-col gap-2 text-sm">
                  <label className="flex items-center gap-2">
                    <Checkbox
                      checked={reportingOptions.plots}
                      onCheckedChange={(checked) =>
                        setReportingOptions((prev) => ({
                          ...prev,
                          plots: !!checked,
                        }))
                      }
                    />
                    Plots
                  </label>
                  <label className="flex items-center gap-2">
                    <Checkbox
                      checked={reportingOptions.denormalize}
                      onCheckedChange={(checked) =>
                        setReportingOptions((prev) => ({
                          ...prev,
                          denormalize: !!checked,
                        }))
                      }
                    />
                    Denormalize state
                  </label>
                  <label className="flex items-center gap-2">
                    <Checkbox
                      checked={reportingOptions.export}
                      onCheckedChange={(checked) =>
                        setReportingOptions((prev) => ({
                          ...prev,
                          export: !!checked,
                        }))
                      }
                    />
                    Export
                  </label>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </CustomPage>
  )
}

export default ExperimentConfigurator
