const defaultHost = '127.0.0.1'

export const getBaseHost = (): string => {
  return import.meta.env.VITE_BACKEND_URL
    ? 'http://' + import.meta.env.VITE_BACKEND_URL
    : 'http://' + defaultHost
}
