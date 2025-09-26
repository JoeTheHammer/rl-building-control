import type { ComponentPropsWithoutRef } from 'react'
import { cn } from '@/lib/utils.ts'
import { useMemo } from 'react'
import MonacoEditor from '@monaco-editor/react'
import type { OnChange, EditorProps as MonacoProps } from '@monaco-editor/react'

export interface FallbackEditorOptions {
  minimap?: { enabled?: boolean }
  fontSize?: number
  automaticLayout?: boolean
}

// Omit 'onChange' so we can redefine it
interface EditorProps
  extends Omit<ComponentPropsWithoutRef<'div'>, 'onChange'> {
  height?: string
  defaultLanguage?: string
  theme?: string
  value?: string
  onChange?: (value: string | undefined) => void
  options?: FallbackEditorOptions
}

const CustomEditor = ({
  className,
  height = '290px',
  defaultLanguage = 'javascript',
  theme = 'vs-dark',
  value = '',
  onChange,
  options,
  ...props
}: EditorProps) => {
  const mergedOptions = useMemo<MonacoProps['options']>(
    () => ({
      minimap: { enabled: options?.minimap?.enabled ?? false },
      fontSize: options?.fontSize ?? 14,
      automaticLayout: options?.automaticLayout ?? true,
    }),
    [options],
  )

  return (
    <div
      className={cn('h-full w-full', className)}
      style={{ height }}
      {...props}
    >
      <MonacoEditor
        height="100%"
        defaultLanguage={defaultLanguage}
        theme={theme}
        value={value}
        onChange={onChange as OnChange}
        options={mergedOptions}
        language={'python'}
      />
    </div>
  )
}

export default CustomEditor
