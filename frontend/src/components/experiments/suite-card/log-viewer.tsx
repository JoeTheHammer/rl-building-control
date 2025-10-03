import React, { useEffect, useRef } from 'react'

interface LogViewerProps {
  title?: string
  lines: string[]
  loading: boolean
  error?: string | null
}

const LogViewer: React.FC<LogViewerProps> = ({
  title = 'Logs',
  lines,
  loading,
  error,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    container.scrollTop = container.scrollHeight
  }, [lines])

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-primary text-base font-semibold">{title}</h3>
      </div>
      <div className="border-muted/40 bg-muted/40 relative max-h-64 overflow-hidden rounded-md border">
        <div ref={containerRef} className="max-h-64 space-y-2 overflow-y-auto p-3">
          {loading ? (
            <p className="text-muted-foreground text-sm">Loading logs…</p>
          ) : (
            <>
              {error && <p className="text-destructive text-sm">{error}</p>}
              {lines.length === 0 ? (
                <p className="text-muted-foreground text-sm">No logs available yet.</p>
              ) : (
                <pre className="text-xs leading-relaxed text-muted-foreground whitespace-pre-wrap">
                  {lines.join('\n')}
                </pre>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default LogViewer
