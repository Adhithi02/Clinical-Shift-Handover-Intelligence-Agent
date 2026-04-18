import { Handle, Position } from '@xyflow/react'
import { useDashboard } from '../../store/dashboardStore'

const colorMap = {
  'var(--blue)': '#2563EB',
  'var(--red)': '#DC2626',
  'var(--amber)': '#D97706',
  'var(--green)': '#059669',
  'var(--teal)': '#0891B2',
}

const dimMap = {
  'var(--blue)': '#DBEAFE',
  'var(--red)': '#FEE2E2',
  'var(--amber)': '#FEF3C7',
  'var(--green)': '#D1FAE5',
  'var(--teal)': '#CFFAFE',
}

export default function AgentNode({ data }) {
  const { state } = useDashboard()
  const nodeStatus = state.nodeStates[data.nodeId] || 'pending'
  const color = colorMap[data.color] || '#94A3B8'
  const dim = dimMap[data.color] || '#F7FAFC'

  let className = 'agent-node'
  let borderColor = '#E2E8F0'
  let bg = '#FFFFFF'
  let statusIcon = null

  if (nodeStatus === 'pending') {
    className += ' agent-node--pending'
  } else if (nodeStatus === 'running') {
    className += ' agent-node--running'
    borderColor = color
    statusIcon = <div className="spinner spinner-sm" style={{ borderTopColor: color, borderColor: dim }} />
  } else if (nodeStatus === 'complete') {
    className += ' agent-node--complete'
    borderColor = color
    bg = dim
    statusIcon = <span className="agent-node__status-icon" style={{ color }}>✓</span>
  } else if (nodeStatus === 'error') {
    className += ' agent-node--error'
    statusIcon = <span className="agent-node__status-icon" style={{ color: '#DC2626' }}>×</span>
  }

  const runningStyle = nodeStatus === 'running' ? {
    borderColor: color,
    boxShadow: `0 0 0 4px ${color}22`,
  } : {}

  const afterStyle = nodeStatus === 'running' ? {
    '--ring-color': color,
  } : {}

  return (
    <div
      className={className}
      style={{ borderColor, background: bg, ...runningStyle, ...afterStyle }}
    >
      <Handle type="target" position={Position.Top} style={{ background: '#94A3B8', border: 'none', width: 6, height: 6 }} />
      <div className="agent-node__top">
        <span className="agent-node__type">{data.type}</span>
        {statusIcon}
      </div>
      <div className="agent-node__name">{data.label}</div>
      {(nodeStatus === 'running' || nodeStatus === 'complete') && data.sub && (
        <div className="agent-node__sub">{data.sub}</div>
      )}
      <Handle type="source" position={Position.Bottom} style={{ background: '#94A3B8', border: 'none', width: 6, height: 6 }} />
    </div>
  )
}
