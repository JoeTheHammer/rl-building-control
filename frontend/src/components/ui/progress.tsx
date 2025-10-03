import React from 'react'

import { cn } from '@/lib/utils.ts'

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: number
  max?: number
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, max = 100, children, ...props }, ref) => {
    const clampedMax = max <= 0 ? 100 : max
    const clampedValue = Math.min(Math.max(value, 0), clampedMax)
    const percentage = (clampedValue / clampedMax) * 100

    return (
      <div
        ref={ref}
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(percentage)}
        className={cn(
          'bg-secondary/60 relative h-3 w-full overflow-hidden rounded-full',
          className,
        )}
        {...props}
      >
        <div
          className="bg-primary h-full transition-all duration-300 ease-out"
          style={{ width: `${percentage}%` }}
        />
        {children}
      </div>
    )
  },
)
Progress.displayName = 'Progress'

export { Progress }
