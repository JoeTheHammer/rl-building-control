const defaultHost = '127.0.0.1'

export const getBaseHost = (): string => {
  return 'http://' + import.meta.env.VITE_BACKEND_URL || defaultHost
}
