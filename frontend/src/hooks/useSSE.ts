import { useEffect, useRef } from 'react'

interface UseSSEOptions {
  onMessage: (event: MessageEvent) => void
  onError?: (event: Event) => void
  enabled?: boolean
}

export function useSSE(url: string, options: UseSSEOptions) {
  const { onMessage, onError, enabled = true } = options
  const esRef = useRef<EventSource | null>(null)
  const onMessageRef = useRef(onMessage)
  const onErrorRef = useRef(onError)

  // Keep refs current
  onMessageRef.current = onMessage
  onErrorRef.current = onError

  useEffect(() => {
    if (!enabled || !url) return

    const es = new EventSource(url)
    esRef.current = es

    es.onmessage = (e) => onMessageRef.current(e)
    es.onerror = (e) => {
      onErrorRef.current?.(e)
    }

    return () => {
      es.close()
      esRef.current = null
    }
  }, [url, enabled])

  const close = () => {
    esRef.current?.close()
    esRef.current = null
  }

  return { close }
}
