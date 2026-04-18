import { useState, useEffect, useRef } from 'react'
import { useDashboard } from '../../store/dashboardStore'

const AGENT_COLORS = {
  PLANNER: 'var(--blue)',
  RISK: 'var(--red)',
  RISK_FLAG: 'var(--red)',
  MISSING: 'var(--amber)',
  MISSING_INFO: 'var(--amber)',
  SYNTHESIS: 'var(--teal)',
  SYSTEM: 'var(--text-muted)',
  ORCHESTRATOR: 'var(--text-muted)',
}

const FILTERS = ['ALL', 'PLANNER', 'RISK', 'MISSING', 'SYNTHESIS']

const DEMO_LOGS = [
  { id: 1,  timestamp: '14:23:07', agent: 'PLANNER',   message: 'Initialising triage scan...', status: 'running' },
  { id: 2,  timestamp: '14:23:08', agent: 'PLANNER',   message: 'Reading patient_a.pdf', status: 'running' },
  { id: 3,  timestamp: '14:23:09', agent: 'PLANNER',   message: 'Reading patient_b.pdf', status: 'running' },
  { id: 4,  timestamp: '14:23:09', agent: 'PLANNER',   message: 'Reading patient_c.pdf', status: 'running' },
  { id: 5,  timestamp: '14:23:11', agent: 'PLANNER',   message: 'Patient B: declining BP trend detected', status: 'running' },
  { id: 6,  timestamp: '14:23:11', agent: 'PLANNER',   message: 'Routing B → RISK_FLAG agent', status: 'complete' },
  { id: 7,  timestamp: '14:23:12', agent: 'PLANNER',   message: 'Patient A: post-op pain score missing', status: 'running' },
  { id: 8,  timestamp: '14:23:12', agent: 'PLANNER',   message: 'Routing A → MISSING_INFO agent', status: 'complete' },
  { id: 9,  timestamp: '14:23:12', agent: 'PLANNER',   message: 'Patient C: all fields complete', status: 'running' },
  { id: 10, timestamp: '14:23:12', agent: 'PLANNER',   message: 'Routing C → SYNTHESIS (direct)', status: 'complete' },
  { id: 11, timestamp: '14:23:13', agent: 'RISK',      message: 'Analysing vital sequence for B...', status: 'running' },
  { id: 12, timestamp: '14:23:13', agent: 'MISSING',   message: 'Auditing documentation for A...', status: 'running' },
  { id: 13, timestamp: '14:23:15', agent: 'RISK',      message: '✓ HIGH RISK — 4-reading BP decline', status: 'complete' },
  { id: 14, timestamp: '14:23:16', agent: 'MISSING',   message: '✓ Missing: post-op pain score (14:00+)', status: 'complete' },
  { id: 15, timestamp: '14:23:17', agent: 'SYNTHESIS', message: 'Generating SBAR briefs...', status: 'running' },
  { id: 16, timestamp: '14:23:19', agent: 'SYNTHESIS', message: '✓ Patient C complete', status: 'complete' },
  { id: 17, timestamp: '14:23:22', agent: 'SYNTHESIS', message: '✓ Patient A complete', status: 'complete' },
  { id: 18, timestamp: '14:23:24', agent: 'SYNTHESIS', message: '✓ Patient B complete — HIGH RISK', status: 'complete' },
]

export default function MessageFeed() {
  const { state } = useDashboard()
  const [filter, setFilter] = useState('ALL')
  const containerRef = useRef(null)

  const allLogs = state.systemStatus === 'idle' && state.logEntries.length === 0 
    ? DEMO_LOGS 
    : state.logEntries
  const filtered = filter === 'ALL' ? allLogs : allLogs.filter(e => {
    const a = e.agent?.toUpperCase() || ''
    if (filter === 'RISK') return a.includes('RISK')
    if (filter === 'MISSING') return a.includes('MISSING')
    return a.includes(filter)
  })

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [filtered.length])

  return (
    <div className="dashboard__col">
      <div className="panel-header">
        <span className="panel-header__title">AGENT LOG</span>
        <span className="panel-header__right">{allLogs.length} entries</span>
      </div>
      <div className="feed-filters">
        {FILTERS.map(f => (
          <button
            key={f}
            className={`feed-filter-pill ${filter === f ? 'feed-filter-pill--active' : ''}`}
            onClick={() => setFilter(f)}
          >{f}</button>
        ))}
      </div>
      <div className="feed-container" ref={containerRef}>
        {filtered.map((entry) => {
          const agentColor = AGENT_COLORS[entry.agent] || 'var(--text-muted)'
          let statusIcon = null
          if (entry.status === 'running') {
            statusIcon = <div className="pulse-dot" style={{ width: 6, height: 6 }} />
          } else if (entry.status === 'complete') {
            statusIcon = <span style={{ color: 'var(--green)', fontSize: 10, fontWeight: 600 }}>✓</span>
          } else if (entry.status === 'error') {
            statusIcon = <span style={{ color: 'var(--red)', fontSize: 10, fontWeight: 600 }}>×</span>
          }

          return (
            <div className="feed-entry" key={entry.id}>
              <span className="feed-entry__time">{entry.timestamp}</span>
              <span className="feed-entry__agent" style={{ color: agentColor }}>{entry.agent}</span>
              <span className="feed-entry__msg">{entry.message}</span>
              <span className="feed-entry__icon">{statusIcon}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
