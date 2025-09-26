import type { ComponentPropsWithoutRef } from 'react'
import { cn } from '@/lib/utils.ts'

export interface FallbackEditorOptions {
  minimap?: { enabled?: boolean }
  fontSize?: number
  automaticLayout?: boolean
}

interface EditorProps extends ComponentPropsWithoutRef<'textarea'> {
  height?: string
  defaultLanguage?: string
  theme?: string
  value?: string
  onChange?: (value: string | undefined) => void
  options?: FallbackEditorOptions
}

const Editor = ({
  className,
  height = '240px',
  value = '',
  onChange,
  options,
  ...props
}: EditorProps) => {
  const lineHeight = options?.fontSize ? options.fontSize * 1.5 : 20

  return (
    <textarea
      className={cn(
        'h-full w-full resize-none bg-background p-4 font-mono text-sm text-foreground outline-none',
        className,
      )}
      style={{ height, lineHeight: `${lineHeight}px` }}
      value={value}
      onChange={(event) => onChange?.(event.target.value)}
      spellCheck={false}
      {...props}
    />
  )
}

export default Editor
