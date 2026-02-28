import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { HomePage } from './pages/HomePage'
import { AnalysisPage } from './pages/AnalysisPage'
import { AlertsPage } from './pages/AlertsPage'
import { WatchlistPage } from './pages/WatchlistPage'
import { MonitorPage } from './pages/MonitorPage'
import { SettingsPage } from './pages/SettingsPage'
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
          return
        }

        if (event.event_type === 'watchlist_price_anomaly' && event.payload?.message) {
          const pct: number = event.payload.change_pct ?? 0
          const isUp = pct >= 0
          const icon = Math.abs(pct) >= 2 ? (isUp ? '📈' : '📉') : (isUp ? '▲' : '▼')
          addNotification(`${icon} ${event.payload.message}`, isUp ? 'success' : 'error')
          return
        }

        if (event.event_type === 'watchlist_news_alert' && event.payload?.message) {
          const icon = event.payload.significance === 'high' ? '🔴' : '🟡'
          addNotification(`${icon} ${event.payload.message}`, 'warning')
          return
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
          <Route path="/monitor" element={<MonitorPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
      <NotificationToast />
    </BrowserRouter>
  )
}
