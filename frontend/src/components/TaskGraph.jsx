import { useCallback, useMemo, useEffect } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  MarkerType,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

// Premium SVG Icons
const AGENT_ICONS = {
  upload: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="17 8 12 3 7 8"/>
      <line x1="12" y1="3" x2="12" y2="15"/>
    </svg>
  ),
  planner: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
      <line x1="3" y1="9" x2="21" y2="9"/>
      <line x1="9" y1="21" x2="9" y2="9"/>
    </svg>
  ),
  risk: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
      <line x1="12" y1="9" x2="12" y2="13"/>
      <line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>
  ),
  missing: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8"/>
      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      <path d="M11 8a2 2 0 0 0-2 2"/>
    </svg>
  ),
  synthesis: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/>
      <polyline points="10 9 9 9 8 9"/>
    </svg>
  )
}

const AGENT_LABELS = {
  planner: 'Planner',
  risk: 'Risk Flag',
  missing: 'Missing Info',
  synthesis: 'Synthesis',
  upload: 'Upload',
}

// Custom Node Component
function AgentNode({ data }) {
  const { agent, patient, patientName, status, message, color } = data

  let nodeClass = 'agent-node'
  if (status === 'running') {
    nodeClass += ' running'
  } else if (status === 'complete') {
    nodeClass += ` complete-${color || 'GREEN'}`
  } else {
    nodeClass += ' pending'
  }

  const getAgentType = (type) => {
    if (!type) return 'unknown'
    const t = type.toLowerCase()
    if (t.includes('upload')) return 'upload'
    if (t.includes('planner')) return 'planner'
    if (t.includes('risk')) return 'risk'
    if (t.includes('missing')) return 'missing'
    if (t.includes('synthesis')) return 'synthesis'
    return type
  }

  const normalizedType = getAgentType(agent)

  return (
    <div className={nodeClass}>
      <Handle type="target" position={Position.Top} style={{ background: '#555', border: 'none', width: 8, height: 8 }} />
      <div className="node-icon">{AGENT_ICONS[normalizedType] || '🔹'}</div>
      <div className="node-agent-name">{AGENT_LABELS[normalizedType] || agent}</div>
      <div className="node-patient">{patientName || patient}</div>
      {status === 'running' && (
        <div className="node-status-text" title={message}>
          {message?.substring(0, 30) || 'Processing...'}
        </div>
      )}
      {status === 'complete' && (
        <div className="node-status-text">Complete</div>
      )}
      <Handle type="source" position={Position.Bottom} style={{ background: '#555', border: 'none', width: 8, height: 8 }} />
    </div>
  )
}

const nodeTypes = { agentNode: AgentNode }

function TaskGraph({ taskGraph, nodeStates, workflowStatus }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  // Build graph from task graph and node states
  useEffect(() => {
    if (!taskGraph || taskGraph.length === 0) {
      if (workflowStatus === 'idle') {
        setNodes([])
        setEdges([])
      }
      return
    }

    const newNodes = []
    const newEdges = []
    
    const patientCount = taskGraph.length
    const spacing = 280
    const startX = -(patientCount - 1) * spacing / 2

    taskGraph.forEach((patient, index) => {
      const patientId = patient.patient_id
      const patientName = patient.name || patient.patient_name || patientId
      const route = patient.route
      const rawAgents = patient.agents || patient.agents_to_invoke || [route, 'synthesis']
      const agents = Array.isArray(rawAgents) ? rawAgents : (typeof rawAgents === 'string' ? rawAgents.split('|') : [rawAgents])
      
      const x = index * spacing
      let y = 0

      // Upload/Start node
      const uploadNodeId = `upload-${patientId}`
      newNodes.push({
        id: uploadNodeId,
        type: 'agentNode',
        position: { x, y },
        data: {
          agent: 'upload',
          patient: patientId,
          patientName: patientName,
          status: 'complete',
          color: 'GREEN'
        }
      })
      y += 120

      // Planner node
      const plannerNodeId = `planner-${patientId}`
      const plannerState = nodeStates[plannerNodeId] || {}
      newNodes.push({
        id: plannerNodeId,
        type: 'agentNode',
        position: { x, y: 120 },
        data: {
          agent: 'planner',
          patient: patientId,
          patientName: patientName,
          status: plannerState.status || 'pending',
          message: plannerState.message || '',
          color: plannerState.result?.color || (plannerState.result?.priority === 'HIGH' ? 'RED' : (plannerState.result?.priority === 'MEDIUM' ? 'AMBER' : 'GREEN'))
        }
      })
      newEdges.push({
        id: `e-upload-planner-${patientId}`,
        source: uploadNodeId,
        target: plannerNodeId,
        animated: plannerState.status === 'running',
        style: { stroke: '#63b3ed', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#63b3ed' }
      })
      y += 120

      // Intermediate agents (risk, missing)
      const intermediateAgents = agents.filter(a => a !== 'synthesis').filter(a => a !== 'planner')
      
      intermediateAgents.forEach((agentType, agentIndex) => {
        const agentNodeId = `${agentType}-${patientId}`
        const agentState = nodeStates[agentNodeId] || {}
        
        // Determine color from result
        let nodeColor = 'GREEN'
        if (agentState.result?.color) {
          nodeColor = agentState.result.color
        } else if (agentState.result?.severity === 'HIGH' || agentState.result?.color === 'RED') {
          nodeColor = 'RED'
        } else if (agentState.result?.severity === 'MEDIUM' || agentState.result?.color === 'AMBER') {
          nodeColor = 'AMBER'
        }
        
        const offsetX = intermediateAgents.length > 1 ? (agentIndex - (intermediateAgents.length - 1) / 2) * 100 : 0
        
        newNodes.push({
          id: agentNodeId,
          type: 'agentNode',
          position: { x: x + offsetX, y },
          data: {
            agent: agentType,
            patient: patientId,
            patientName: patientName,
            status: agentState.status || 'pending',
            message: agentState.message || '',
            color: nodeColor
          }
        })

        const normalizedAgent = agentType.toLowerCase().includes('risk') ? 'risk' : (agentType.toLowerCase().includes('missing') ? 'missing' : agentType)
        
        // Edge from planner
        newEdges.push({
          id: `e-planner-${agentType}-${patientId}`,
          source: plannerNodeId,
          target: agentNodeId,
          animated: agentState.status === 'running',
          style: { 
            stroke: normalizedAgent === 'risk' ? '#ef4444' : normalizedAgent === 'missing' ? '#f59e0b' : '#63b3ed',
            strokeWidth: 2 
          },
          markerEnd: { 
            type: MarkerType.ArrowClosed, 
            color: normalizedAgent === 'risk' ? '#ef4444' : normalizedAgent === 'missing' ? '#f59e0b' : '#63b3ed'
          }
        })
      })

      // Synthesis node
      const synthY = intermediateAgents.filter(a => a !== 'planner').length > 0 ? y + 120 : y
      const synthNodeId = `synthesis-${patientId}`
      const synthState = nodeStates[synthNodeId] || {}
      
      let synthColor = 'GREEN'
      if (synthState.result?.color) synthColor = synthState.result.color
      
      newNodes.push({
        id: synthNodeId,
        type: 'agentNode',
        position: { x, y: synthY },
        data: {
          agent: 'synthesis',
          patient: patientId,
          patientName: patientName,
          status: synthState.status || 'pending',
          message: synthState.message || '',
          color: synthColor
        }
      })

      // Edges to synthesis
      const sourceAgents = intermediateAgents.filter(a => a !== 'planner')
      if (sourceAgents.length > 0) {
        sourceAgents.forEach(agentType => {
          newEdges.push({
            id: `e-${agentType}-synth-${patientId}`,
            source: `${agentType}-${patientId}`,
            target: synthNodeId,
            animated: synthState.status === 'running',
            style: { stroke: '#10b981', strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed, color: '#10b981' }
          })
        })
      } else {
        // Direct from planner to synthesis
        newEdges.push({
          id: `e-planner-synth-${patientId}`,
          source: plannerNodeId,
          target: synthNodeId,
          animated: synthState.status === 'running',
          style: { stroke: '#10b981', strokeWidth: 2 },
          markerEnd: { type: MarkerType.ArrowClosed, color: '#10b981' }
        })
      }
    })

    setNodes(newNodes)
    setEdges(newEdges)
  }, [taskGraph, nodeStates, workflowStatus, setNodes, setEdges])

  if (nodes.length === 0) {
    return (
      <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
        <div style={{ fontSize: '13px', fontWeight: 500 }}>No workflow active</div>
        <div style={{ fontSize: '12px', marginTop: '4px' }}>Upload patient PDFs or load demo data to see the live task graph</div>
      </div>
    )
  }

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.3 }}
      proOptions={{ hideAttribution: true }}
      style={{ background: 'transparent' }}
      minZoom={0.3}
      maxZoom={1.5}
    >
      <Background color="#cbd5e1" gap={20} size={1} />
      <Controls 
        style={{ 
          background: 'var(--bg-surface)', 
          border: '1px solid var(--border-subtle)',
          borderRadius: '8px',
          boxShadow: 'var(--shadow-card)'
        }}
      />
    </ReactFlow>
  )
}

export default TaskGraph
