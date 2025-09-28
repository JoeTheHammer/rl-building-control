import type { ReactNode, RefObject } from 'react'
import { Save, Code2, Monitor, Import, FolderOpen } from 'lucide-react'
import CustomPage from '../../shared/page.tsx'
import { Button } from '../../ui/button.tsx'

interface ControllerToolbarProps {
  devMode: boolean
  onToggleDevMode: () => void
  onSave: () => void
  onUpload: () => void
  onOpenConfig: () => void
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  fileInputRef: RefObject<HTMLInputElement | null>
  children: ReactNode
}

const ControllerToolbar = ({
  devMode,
  onToggleDevMode,
  onSave,
  onUpload,
  onOpenConfig,
  onFileChange,
  fileInputRef,
  children,
}: ControllerToolbarProps) => (
  <CustomPage>
    <div className="flex w-full flex-col gap-4 pt-2">
      <div className="grid grid-cols-1 items-center gap-2 md:grid-cols-6">
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

        <div className="md:col-start-4">
          <Button
            onClick={onOpenConfig}
            type="button"
            className="text-md w-full"
          >
            <div className="flex items-center gap-2">
              <FolderOpen />
              <span>Open Configuration</span>
            </div>
          </Button>
        </div>

        <div className="md:col-start-5">
          <Button onClick={onUpload} type="button" className="text-md w-full">
            <div className="flex items-center gap-2">
              <Import />
              <span>Import Configuration</span>
            </div>
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".yaml,.yml"
            onChange={onFileChange}
            className="hidden"
          />
        </div>

        <div className="md:col-start-6">
          <Button onClick={onSave} type="button" className="text-md w-full">
            <div className="flex items-center gap-2">
              <Save />
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
