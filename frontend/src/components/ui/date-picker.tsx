import { useEffect, useId, useMemo, useRef, useState } from 'react'
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

import { cn } from '../../lib/utils.ts'
import { Button } from './button.tsx'

type DatePickerProps = {
  id?: string
  date?: Date
  onDateChange?: (date: Date | undefined) => void
  placeholder?: string
  className?: string
}

const dayFormatter = new Intl.DateTimeFormat(undefined, { day: 'numeric' })
const valueFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
})
const weekdayFormatter = new Intl.DateTimeFormat(undefined, {
  weekday: 'short',
})

const buildCalendar = (month: Date) => {
  const firstDayOfMonth = new Date(month.getFullYear(), month.getMonth(), 1)
  const startOffset = firstDayOfMonth.getDay()
  const current = new Date(firstDayOfMonth)
  current.setDate(current.getDate() - startOffset)

  const weeks: Date[][] = []
  for (let weekIndex = 0; weekIndex < 6; weekIndex += 1) {
    const days: Date[] = []
    for (let dayIndex = 0; dayIndex < 7; dayIndex += 1) {
      days.push(new Date(current))
      current.setDate(current.getDate() + 1)
    }
    weeks.push(days)
  }

  return weeks
}

const isSameDay = (first: Date | undefined, second: Date | undefined) => {
  if (!first || !second) {
    return false
  }

  return (
    first.getFullYear() === second.getFullYear() &&
    first.getMonth() === second.getMonth() &&
    first.getDate() === second.getDate()
  )
}

const isSameMonth = (first: Date, second: Date) => {
  return (
    first.getFullYear() === second.getFullYear() &&
    first.getMonth() === second.getMonth()
  )
}

const weekdayLabels = Array.from({ length: 7 }, (_, dayIndex) => {
  const baseDate = new Date(2024, 8, dayIndex + 1)
  return weekdayFormatter.format(baseDate)
})

const monthNames = Array.from({ length: 12 }, (_, monthIndex) =>
  new Intl.DateTimeFormat(undefined, { month: 'long' }).format(
    new Date(2000, monthIndex, 1),
  ),
)

const buildYearRange = (year: number) => {
  const currentYear = new Date().getFullYear()
  const start = Math.min(year - 50, currentYear - 50)
  const end = Math.max(year + 50, currentYear + 10)

  return Array.from({ length: end - start + 1 }, (_, index) => start + index)
}

const DatePicker = ({
  id,
  date,
  onDateChange,
  placeholder = 'Pick a date',
  className,
}: DatePickerProps) => {
  const generatedId = useId()
  const [open, setOpen] = useState(false)
  const [displayMonth, setDisplayMonth] = useState<Date>(() => {
    const initial = date ?? new Date()
    return new Date(initial.getFullYear(), initial.getMonth(), 1)
  })
  const containerRef = useRef<HTMLDivElement>(null)
  const controlBaseId = id ?? generatedId
  const monthSelectId = `${controlBaseId}-month`
  const yearSelectId = `${controlBaseId}-year`

  useEffect(() => {
    if (!open) {
      return
    }

    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [open])

  useEffect(() => {
    if (!date) {
      return
    }

    setDisplayMonth(new Date(date.getFullYear(), date.getMonth(), 1))
  }, [date])

  const weeks = useMemo(() => buildCalendar(displayMonth), [displayMonth])
  const yearOptions = useMemo(
    () => buildYearRange(displayMonth.getFullYear()),
    [displayMonth],
  )

  const handleDaySelect = (day: Date) => {
    onDateChange?.(day)
    setOpen(false)
  }

  const handlePrevMonth = () => {
    setDisplayMonth(
      (prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1),
    )
  }

  const handleNextMonth = () => {
    setDisplayMonth(
      (prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1),
    )
  }

  const handleMonthJump = (monthIndex: number) => {
    setDisplayMonth((prev) => new Date(prev.getFullYear(), monthIndex, 1))
  }

  const handleYearJump = (year: number) => {
    setDisplayMonth((prev) => new Date(year, prev.getMonth(), 1))
  }

  return (
    <div className={cn('bg-background relative', className)} ref={containerRef}>
      <Button
        id={id}
        variant="outline"
        className={cn(
          'flex w-full items-center justify-start gap-2 text-left font-normal',
          !date && 'text-muted-foreground',
        )}
        onClick={() => setOpen((prev) => !prev)}
        type="button"
        aria-haspopup="dialog"
        aria-expanded={open}
      >
        <CalendarIcon className="h-4 w-4" />
        {date ? valueFormatter.format(date) : <span>{placeholder}</span>}
      </Button>
      {open && (
        <div className="bg-background absolute top-full left-0 z-50 mt-2 w-72 rounded-md border p-3 shadow-lg">
          <div className="text-primary flex items-center justify-between gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={handlePrevMonth}
              type="button"
              aria-label="Previous month"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="flex flex-1 items-center justify-center gap-2 text-sm font-medium">
              <label className="sr-only" htmlFor={monthSelectId}>
                Month
              </label>
              <select
                id={monthSelectId}
                className="border-input bg-background focus:ring-primary h-8 min-w-[6rem] rounded-md border px-2 text-sm font-medium focus:ring-2 focus:outline-none"
                value={displayMonth.getMonth()}
                onChange={(event) =>
                  handleMonthJump(Number(event.target.value))
                }
              >
                {monthNames.map((name, index) => (
                  <option key={name} value={index}>
                    {name}
                  </option>
                ))}
              </select>
              <label className="sr-only" htmlFor={yearSelectId}>
                Year
              </label>
              <select
                id={yearSelectId}
                className="border-input bg-background focus:ring-primary h-8 min-w-[5rem] rounded-md border px-2 text-sm font-medium focus:ring-2 focus:outline-none"
                value={displayMonth.getFullYear()}
                onChange={(event) => handleYearJump(Number(event.target.value))}
              >
                {yearOptions.map((yearOption) => (
                  <option key={yearOption} value={yearOption}>
                    {yearOption}
                  </option>
                ))}
              </select>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleNextMonth}
              type="button"
              aria-label="Next month"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
          <div className="text-muted-foreground mt-3 grid grid-cols-7 gap-1 text-center text-xs font-medium">
            {weekdayLabels.map((label) => (
              <span key={label}>{label}</span>
            ))}
          </div>
          <div className="text-primary mt-1 grid grid-cols-7 gap-1 text-center text-sm">
            {weeks.map((week, weekIndex) =>
              week.map((day) => {
                const isCurrentMonth = isSameMonth(day, displayMonth)
                const selected = isSameDay(day, date)
                return (
                  <button
                    key={`${weekIndex}-${day.toISOString()}`}
                    type="button"
                    onClick={() => handleDaySelect(day)}
                    className={cn(
                      'hover:bg-primary hover:text-primary-foreground h-9 w-full cursor-pointer rounded-md border border-transparent transition-colors',
                      selected
                        ? 'bg-primary text-primary-foreground shadow'
                        : isCurrentMonth
                          ? ''
                          : '',
                    )}
                  >
                    {dayFormatter.format(day)}
                  </button>
                )
              }),
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export { DatePicker }
