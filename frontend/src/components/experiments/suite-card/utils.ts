import type {
  ExperimentRunStatusResponse,
  ExperimentSuiteStatus,
} from '@/services/experiment-service.ts'

export const getStatusBadgeClass = (status: ExperimentSuiteStatus): string => {
  switch (status) {
    case 'Running':
      return 'bg-emerald-500 text-white'
    case 'Finished':
      return 'bg-green-800 text-primary-foreground'
    case 'Aborted':
      return 'bg-red-800 text-primary-foreground'
    default:
      return 'bg-secondary text-secondary-foreground'
  }
}

export const getFileName = (path?: string): string => {
  if (!path) return 'Unknown'
  const segments = path.split('/')
  return segments[segments.length - 1] ?? path
}

const isProgressLine = (line: string): boolean =>
  line.trim().toLowerCase().startsWith('simulation progress')

export const splitLines = (content: string): string[] => {
  const normalized = content.replace(/\r\n/g, '\n')
  const lines = normalized.split('\n')
  if (lines.length && lines[lines.length - 1] === '') {
    lines.pop()
  }
  return lines
}

export const mergeLogLines = (current: string[], incoming: string[]): string[] => {
  if (incoming.length === 0) return current
  const next = [...current]
  for (const line of incoming) {
    if (line === '' && next.length === 0) {
      continue
    }
    if (
      isProgressLine(line) &&
      next.length > 0 &&
      isProgressLine(next[next.length - 1])
    ) {
      next[next.length - 1] = line
    } else {
      next.push(line)
    }
  }
  return next
}

export const buildProgressById = (
  statusInfo: ExperimentRunStatusResponse | null,
): Map<number, ExperimentRunStatusResponse['experiments'][number]> => {
  const map = new Map<
    number,
    ExperimentRunStatusResponse['experiments'][number]
  >()
  const experiments = statusInfo?.experiments ?? []
  for (const entry of experiments) {
    map.set(entry.id, entry)
  }
  return map
}
