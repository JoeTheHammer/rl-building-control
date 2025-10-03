import type { ComponentPropsWithoutRef } from 'react'
import { cn } from '@/lib/utils.ts'
import { useMemo, useEffect, useRef } from 'react'
import MonacoEditor from '@monaco-editor/react'
import type {
  OnChange,
  EditorProps as MonacoProps,
  OnMount,
} from '@monaco-editor/react'
import type * as monaco from 'monaco-editor'
import { languages } from 'monaco-editor'

export interface FallbackEditorOptions {
  minimap?: { enabled?: boolean }
  fontSize?: number
  automaticLayout?: boolean
  readOnly?: boolean
}

interface EditorProps
  extends Omit<ComponentPropsWithoutRef<'div'>, 'onChange'> {
  height?: string
  defaultLanguage?: string
  theme?: string
  value?: string
  onChange?: (value: string | undefined) => void
  options?: FallbackEditorOptions
  /** Array of strings for auto-complete suggestions */
  knownWords?: string[]
}

const CustomEditor = ({
  className,
  height = '250px',
  defaultLanguage = 'python',
  theme = 'vs-dark',
  value = '',
  onChange,
  options,
  knownWords = [],
  ...props
}: EditorProps) => {
  const monacoRef = useRef<typeof monaco | null>(null)

  const mergedOptions = useMemo<MonacoProps['options']>(
    () => ({
      minimap: { enabled: options?.minimap?.enabled ?? false },
      fontSize: options?.fontSize ?? 14,
      automaticLayout: options?.automaticLayout ?? true,
      readOnly: options?.readOnly ?? false,
    }),
    [options],
  )

  const handleMount: OnMount = (_editor, monacoInstance) => {
    monacoRef.current = monacoInstance
  }

  // Re-register completion provider when knownWords change
  useEffect(() => {
    if (!monacoRef.current) return

    const monaco = monacoRef.current

    // ensure uniqueness
    const uniqueWords = Array.from(new Set(knownWords))

    const provider = monaco.languages.registerCompletionItemProvider(
      defaultLanguage,
      {
        provideCompletionItems: (model, position) => {
          const word = model.getWordUntilPosition(position)
          const range = new monaco.Range(
            position.lineNumber,
            word.startColumn,
            position.lineNumber,
            word.endColumn,
          )

          const suggestions: languages.CompletionItem[] = uniqueWords.map(
            (w) => ({
              label: w,
              kind: monaco.languages.CompletionItemKind.Text,
              insertText: w,
              range,
            }),
          )

          return { suggestions }
        },
      },
    )

    return () => {
      provider.dispose()
    }
  }, [knownWords, defaultLanguage])

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
        onMount={handleMount}
      />
    </div>
  )
}

export default CustomEditor
