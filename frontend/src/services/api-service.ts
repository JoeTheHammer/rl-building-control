const DEFAULT_BACKEND_PORT = '8000'

const normalizeConfiguredBackendOrigin = (value: string): string | null => {
  const trimmed = value.trim()
  if (!trimmed) return null

  const withProtocol = trimmed.includes('://')
    ? trimmed
    : `${window.location.protocol}//${trimmed}`

  try {
    const url = new URL(withProtocol)
    if (!url.port && !trimmed.includes(':')) {
      url.port = DEFAULT_BACKEND_PORT
    }
    return url.origin
  } catch {
    return null
  }
}

export const getBackendOrigin = (): string => {
  const configured = import.meta.env.VITE_BACKEND_URL
  if (configured) {
    const origin = normalizeConfiguredBackendOrigin(configured)
    if (origin) {
      return origin
    }
  }

  const host = window.location.hostname || '127.0.0.1'
  return `${window.location.protocol}//${host}:${DEFAULT_BACKEND_PORT}`
}

export const getApiBase = (path: string): string => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${getBackendOrigin()}${normalizedPath}`
}

// Backward compatibility for older service files that still append ":8000".
export const getBaseHost = (): string => {
  const configured = import.meta.env.VITE_BACKEND_URL
  const fallbackHost = window.location.hostname || '127.0.0.1'

  if (!configured || configured.trim() === '') {
    return `${window.location.protocol}//${fallbackHost}`
  }

  const trimmed = configured.trim()
  const withProtocol = trimmed.includes('://')
    ? trimmed
    : `${window.location.protocol}//${trimmed}`

  try {
    const url = new URL(withProtocol)
    return `${url.protocol}//${url.hostname}`
  } catch {
    return `${window.location.protocol}//${fallbackHost}`
  }
}
