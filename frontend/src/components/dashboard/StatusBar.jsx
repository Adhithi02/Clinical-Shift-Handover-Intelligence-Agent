import { useEffect } from 'react'
import { useDashboard } from '../../store/dashboardStore'

export default function StatusBar() {
  const { state, dispatch } = useDashboard()

  useEffect(() => {
    let interval
    if (state.systemStatus === 'running') {
      interval = setInterval(() => {
        dispatch({ type: 'TICK_RUNTIME' })
      }, 1000)
    }
    return () => clearInterval(interval)
  }, [state.systemStatus, dispatch])

  const pad = (n) => String(n).padStart(2, '0')
  const hrs = pad(Math.floor(state.runtime / 3600))
  const mins = pad(Math.floor((state.runtime % 3600) / 60))
  const secs = pad(state.runtime % 60)

  const progressPct = (state.progress / 3) * 100

  return (
    <div className="statusbar">
      <div className="statusbar__left">
        <div className="pulse-dot" style={{ width: 6, height: 6 }} />
        SYSTEM ACTIVE
      </div>
      <div className="statusbar__center">
        <span>{state.progress}/3 PATIENTS</span>
        <div className="statusbar__progress">
          <div className="statusbar__progress-fill" style={{ width: `${progressPct}%` }} />
        </div>
      </div>
      <div className="statusbar__right">
        {hrs}:{mins}:{secs}
      </div>
    </div>
  )
}
