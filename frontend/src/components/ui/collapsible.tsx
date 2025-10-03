import React, {
  createContext,
  useCallback,
  useContext,
  useId,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from 'react'

import { cn } from '@/lib/utils.ts'

type CollapsibleContextValue = {
  open: boolean
  setOpen: (open: boolean) => void
  toggle: () => void
  triggerId: string
  contentId: string
}

const CollapsibleContext = createContext<CollapsibleContextValue | null>(null)

const useCollapsibleContext = (): CollapsibleContextValue => {
  const context = useContext(CollapsibleContext)
  if (!context) {
    throw new Error('Collapsible components must be used within <Collapsible>')
  }
  return context
}

interface CollapsibleProps extends React.HTMLAttributes<HTMLDivElement> {
  open?: boolean
  defaultOpen?: boolean
  onOpenChange?: (open: boolean) => void
}

const Collapsible: React.FC<CollapsibleProps> = ({
  open,
  defaultOpen = false,
  onOpenChange,
  className,
  children,
  ...props
}) => {
  const isControlled = typeof open === 'boolean'
  const [internalOpen, setInternalOpen] = useState(defaultOpen)
  const currentOpen = isControlled ? (open as boolean) : internalOpen

  const setOpen = useCallback(
    (next: boolean) => {
      if (!isControlled) {
        setInternalOpen(next)
      }
      onOpenChange?.(next)
    },
    [isControlled, onOpenChange],
  )

  const toggle = useCallback(() => {
    setOpen(!currentOpen)
  }, [currentOpen, setOpen])

  const triggerId = useId()
  const contentId = useId()

  const value = useMemo(
    () => ({
      open: currentOpen,
      setOpen,
      toggle,
      triggerId,
      contentId,
    }),
    [contentId, currentOpen, setOpen, toggle, triggerId],
  )

  return (
    <CollapsibleContext.Provider value={value}>
      <div
        className={cn(className)}
        data-state={currentOpen ? 'open' : 'closed'}
        {...props}
      >
        {children}
      </div>
    </CollapsibleContext.Provider>
  )
}

interface CollapsibleTriggerProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean
}

const CollapsibleTrigger = React.forwardRef<HTMLButtonElement, CollapsibleTriggerProps>(
  ({ asChild = false, className, children, onClick, ...props }, ref) => {
    const { open, toggle, triggerId, contentId } = useCollapsibleContext()

    const handleClick = useCallback<React.MouseEventHandler<HTMLButtonElement>>(
      (event) => {
        onClick?.(event)
        if (!event.defaultPrevented) {
          toggle()
        }
      },
      [onClick, toggle],
    )

    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children, {
        ref,
        id: triggerId,
        'aria-expanded': open,
        'aria-controls': contentId,
        onClick: (event: React.MouseEvent<HTMLElement>) => {
          const childOnClick = (children as React.ReactElement).props.onClick
          childOnClick?.(event)
          if (!event.defaultPrevented) {
            toggle()
          }
        },
      })
    }

    return (
      <button
        ref={ref}
        type="button"
        id={triggerId}
        aria-expanded={open}
        aria-controls={contentId}
        className={className}
        onClick={handleClick}
        {...props}
      >
        {children}
      </button>
    )
  },
)
CollapsibleTrigger.displayName = 'CollapsibleTrigger'

interface CollapsibleContentProps extends React.HTMLAttributes<HTMLDivElement> {}

const CollapsibleContent = React.forwardRef<HTMLDivElement, CollapsibleContentProps>(
  ({ className, style, children, ...props }, ref) => {
    const { open, contentId } = useCollapsibleContext()
    const innerRef = useRef<HTMLDivElement | null>(null)
    const [height, setHeight] = useState<string>(open ? 'auto' : '0px')
    const [isTransitioning, setIsTransitioning] = useState(false)

    useLayoutEffect(() => {
      const element = innerRef.current
      if (!element) return

      const scrollHeight = element.scrollHeight

      if (open) {
        setIsTransitioning(true)
        setHeight(`${scrollHeight}px`)
        const timeout = window.setTimeout(() => {
          setHeight('auto')
          setIsTransitioning(false)
        }, 300)
        return () => window.clearTimeout(timeout)
      }

      setIsTransitioning(true)
      const currentHeight = element.getBoundingClientRect().height
      setHeight(`${currentHeight}px`)

      const animation = window.requestAnimationFrame(() => {
        setHeight('0px')
      })

      const timeout = window.setTimeout(() => {
        setIsTransitioning(false)
      }, 300)

      return () => {
        window.cancelAnimationFrame(animation)
        window.clearTimeout(timeout)
      }
    }, [open, children])

    return (
      <div
        ref={ref}
        id={contentId}
        data-state={open ? 'open' : 'closed'}
        aria-hidden={!open && !isTransitioning}
        className={cn('overflow-hidden transition-[max-height] duration-300 ease-in-out', className)}
        style={{
          maxHeight: height,
          ...style,
        }}
        {...props}
      >
        <div ref={innerRef}>{children}</div>
      </div>
    )
  },
)
CollapsibleContent.displayName = 'CollapsibleContent'

export { Collapsible, CollapsibleTrigger, CollapsibleContent }
