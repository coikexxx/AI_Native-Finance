import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { AppShell } from './components/layout/AppShell'
import { HomePage } from './pages/HomePage'
import { AnalysisPage } from './pages/AnalysisPage'
import { AlertsPage } from './pages/AlertsPage'
import { WatchlistPage } from './pages/WatchlistPage'
import { NotificationToast } from './components/ui/NotificationToast'
import { useSSE } from './hooks/useSSE'
import { useAnalysisStore } from './store/analysisStore'

function GlobalNotificationListener() {
  const { addNotification } = useAnalysisStore()

  useSSE('/api/v1/alerts/stream', {
    enabled: true,
    onMessage: (e) => {
      try {
        const event = JSON.parse(e.data)
        if (event.event_type === 'alert_triggered' && event.payload?.message) {
          addNotification(`🔔 ${event.payload.message}`, 'info')
        }
      } catch {}
    },
  })

  return null
}

export default function App() {
  return (
    <BrowserRouter>
      <GlobalNotificationListener />
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/analysis/:jobId" element={<AnalysisPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/watchlist" element={<WatchlistPage />} />
        </Route>
      </Routes>
      <NotificationToast />
    </BrowserRouter>
  )
}
