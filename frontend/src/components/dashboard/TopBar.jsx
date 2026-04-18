import { useNavigate } from 'react-router-dom'
import { useDashboard } from '../../store/dashboardStore'

export default function TopBar({ onUploadClick }) {
  const navigate = useNavigate()
  const { state } = useDashboard()

  const statusLabel = state.systemStatus === 'idle' ? 'AGENTS READY'
    : state.systemStatus === 'running' ? 'RUNNING'
    : state.systemStatus === 'complete' ? 'COMPLETE' : 'AGENTS READY'

  return (
    <div className="topbar">
      <div className="topbar__brand">
        <div className="pulse-dot" />
        HANDOVER.AI
      </div>
      <div className="topbar__pills">
        <div className={`status-pill ${state.ollamaConnected ? 'status-pill--active' : 'status-pill--inactive'}`}>
          <div className="status-pill__dot" />
          {state.ollamaConnected ? 'OLLAMA CONNECTED' : 'OLLAMA OFFLINE'}
        </div>
        <div className={`status-pill ${state.patientsLoaded ? 'status-pill--active' : 'status-pill--inactive'}`}>
          <div className="status-pill__dot" />
          {state.patientsLoaded ? '3 PATIENTS LOADED' : 'NO PATIENTS'}
        </div>
        <div className={`status-pill ${state.systemStatus !== 'idle' ? 'status-pill--active' : 'status-pill--inactive'}`}>
          <div className="status-pill__dot" />
          {statusLabel}
        </div>
      </div>
      <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
        <button 
          className="run-btn run-btn--outline" 
          onClick={onUploadClick}
          style={{ padding: '6px 12px', fontSize: '11px' }}
        >
          Upload PDFs
        </button>
        <button className="topbar__back" onClick={() => navigate('/')}>
          ← Back to Overview
        </button>
      </div>
    </div>
  )
}
