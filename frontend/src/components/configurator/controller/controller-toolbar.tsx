import type { ReactNode } from 'react'
import { Save, Code2, Monitor } from 'lucide-react'
import CustomPage from '../../shared/page.tsx'
import { Button } from '../../ui/button.tsx'

interface ControllerToolbarProps {
  devMode: boolean
  onToggleDevMode: () => void
  onSave: () => void
  children: ReactNode
}

const ControllerToolbar = ({
  devMode,
  onToggleDevMode,
  onSave,
  children,
}: ControllerToolbarProps) => (
  <CustomPage>
    <div className="flex w-full flex-col gap-4 pt-2">
      <div className="grid grid-cols-1 items-center gap-2 md:grid-cols-4">
        <div className="md:col-span-2">
          <span className="text-primary text-md font-bold md:text-xl">
            Controller Configurator
          </span>
        </div>
        <div className="md:col-start-3">
          <Button
            onClick={onToggleDevMode}
            type="button"
            variant={devMode ? 'default' : 'ghost'}
            className="text-md flex w-full gap-2 border"
          >
            {devMode ? (
              <>
                <Monitor className="h-4 w-4" />
                Switch to GUI Mode
              </>
            ) : (
              <>
                <Code2 className="h-4 w-4" />
                Switch to Dev Mode
              </>
            )}
          </Button>
        </div>
        <div className="md:col-start-4">
          <Button onClick={onSave} type="button" className="text-md w-full">
            <div className="flex items-center gap-2">
              <Save className="h-4 w-4" />
              <span>Save Configuration</span>
            </div>
          </Button>
        </div>
      </div>

      <hr className="border-t-primary w-full" />

      {children}
    </div>
  </CustomPage>
)

export default ControllerToolbar
