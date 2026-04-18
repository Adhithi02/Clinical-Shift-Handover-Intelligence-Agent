import { useEffect, useRef } from 'react'

function MessageFeed({ messages }) {
  const bottomRef = useRef(null)
  const containerRef = useRef(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  const formatTime = (timestamp) => {
    if (!timestamp) return '--:--'
    try {
      const date = new Date(timestamp)
      return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: false 
      })
    } catch {
      return '--:--'
    }
  }

  const getAgentClass = (agent) => {
    const agentMap = {
      planner: 'planner',
      risk: 'risk',
      missing: 'missing',
      synthesis: 'synthesis',
      orchestrator: 'orchestrator'
    }
    return agentMap[agent] || 'orchestrator'
  }

  const getPatientShort = (patientId) => {
    if (!patientId || patientId === 'all') return 'ALL'
    // Extract letter from patient ID: PAT-A-2024-0471 -> A
    const match = patientId.match(/PAT-([A-Z])/i)
    if (match) return match[1]
    // Fallback: last 4 chars
    return patientId.slice(-4)
  }

  const isHighSeverity = (msg) => {
    if (msg.result?.severity === 'HIGH') return true
    if (msg.result?.color === 'RED') return true
    if (msg.message?.includes('HIGH') || msg.message?.includes('URGENT')) return true
    return false
  }

  // Filter out connection/pong messages
  const visibleMessages = messages.filter(m => 
    m.type !== 'connection' && m.type !== 'pong'
  )

  if (visibleMessages.length === 0) {
    return (
      <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
        <div style={{ fontSize: '13px', fontWeight: 500 }}>Waiting for agent activity</div>
      </div>
    )
  }

  const getSeverityClass = (msg) => {
    if (isHighSeverity(msg)) return 'severity-high'
    if (msg.result?.severity === 'MEDIUM' || msg.result?.color === 'AMBER') return 'severity-med'
    if (msg.status === 'complete') return 'severity-low'
    return 'severity-info'
  }

  return (
    <div className="feed-container" ref={containerRef}>
      {visibleMessages.map((msg, index) => (
        <div key={index} className={`message-card ${getSeverityClass(msg)}`}>
          <div className="msg-header">
            <span className="msg-agent">{msg.agent === 'orchestrator' ? 'System' : msg.agent}</span>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span className="msg-patient">{getPatientShort(msg.patient)}</span>
              <span className="msg-time">{formatTime(msg.timestamp)}</span>
            </div>
          </div>
          <div className="msg-body">
            {msg.message || ''}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}

export default MessageFeed
