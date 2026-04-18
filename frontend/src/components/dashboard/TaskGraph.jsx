import { useMemo, useCallback } from 'react'
import {
  ReactFlow,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import AgentNode from './AgentNode'
import { useDashboard } from '../../store/dashboardStore'

const nodeTypes = { agentNode: AgentNode }

const initialNodes = [
  { id: 'planner',   type: 'agentNode', position: { x: 160, y: 20 },  data: { nodeId: 'planner',   label: 'Planner Agent', type: 'ORCHESTRATOR',  color: 'var(--blue)',  sub: '' } },
  { id: 'patient-a', type: 'agentNode', position: { x: 0,   y: 140 }, data: { nodeId: 'patient-a', label: 'Patient A',     type: 'ARUN MEHTA',    color: 'var(--amber)', sub: '' } },
  { id: 'patient-b', type: 'agentNode', position: { x: 190, y: 140 }, data: { nodeId: 'patient-b', label: 'Patient B',     type: 'PRIYA SHARMA',  color: 'var(--red)',   sub: '' } },
  { id: 'patient-c', type: 'agentNode', position: { x: 380, y: 140 }, data: { nodeId: 'patient-c', label: 'Patient C',     type: 'RAVI KUMAR',    color: 'var(--green)', sub: '' } },
  { id: 'missing',   type: 'agentNode', position: { x: 0,   y: 280 }, data: { nodeId: 'missing',   label: 'Missing Info',  type: 'AGENT',         color: 'var(--amber)', sub: '' } },
  { id: 'risk',      type: 'agentNode', position: { x: 190, y: 280 }, data: { nodeId: 'risk',      label: 'Risk Flag',     type: 'AGENT',         color: 'var(--red)',   sub: '' } },
  { id: 'synthesis', type: 'agentNode', position: { x: 160, y: 400 }, data: { nodeId: 'synthesis', label: 'Synthesis',     type: 'AGENT',         color: 'var(--teal)',  sub: '' } },
  { id: 'output-a',  type: 'agentNode', position: { x: 0,   y: 520 }, data: { nodeId: 'output-a',  label: 'SBAR — A',      type: 'OUTPUT',        color: 'var(--teal)',  sub: '' } },
  { id: 'output-b',  type: 'agentNode', position: { x: 190, y: 520 }, data: { nodeId: 'output-b',  label: 'SBAR — B',      type: 'OUTPUT',        color: 'var(--teal)',  sub: '' } },
  { id: 'output-c',  type: 'agentNode', position: { x: 380, y: 520 }, data: { nodeId: 'output-c',  label: 'SBAR — C',      type: 'OUTPUT',        color: 'var(--teal)',  sub: '' } },
]

const defaultEdgeStyle = {
  stroke: '#E2E8F0',
  strokeDasharray: '4 4',
  strokeWidth: 1.5,
}

const initialEdges = [
  { id: 'e-p-a', source: 'planner', target: 'patient-a', style: defaultEdgeStyle, markerEnd: { type: MarkerType.ArrowClosed, color: '#E2E8F0' } },
  { id: 'e-p-b', source: 'planner', target: 'patient-b', style: defaultEdgeStyle, markerEnd: { type: MarkerType.ArrowClosed, color: '#E2E8F0' } },
  { id: 'e-p-c', source: 'planner', target: 'patient-c', style: defaultEdgeStyle, markerEnd: { type: MarkerType.ArrowClosed, color: '#E2E8F0' } },
  { id: 'e-a-m', source: 'patient-a', target: 'missing',   style: defaultEdgeStyle, markerEnd: { type: MarkerType.ArrowClosed, color: '#E2E8F0' } },
  { id: 'e-b-r', source: 'patient-b', target: 'risk',      style: defaultEdgeStyle, markerEnd: { type: MarkerType.ArrowClosed, color: '#E2E8F0' } },
  { id: 'e-c-s', source: 'patient-c', target: 'synthesis',  style: defaultEdgeStyle, markerEnd: { type: MarkerType.ArrowClosed, color: '#E2E8F0' } },
  { id: 'e-m-s', source: 'missing',   target: 'synthesis',  style: defaultEdgeStyle, markerEnd: { type: MarkerType.ArrowClosed, color: '#E2E8F0' } },
  { id: 'e-r-s', source: 'risk',      target: 'synthesis',  style: defaultEdgeStyle, markerEnd: { type: MarkerType.ArrowClosed, color: '#E2E8F0' } },
  { id: 'e-s-oa', source: 'synthesis', target: 'output-a', style: defaultEdgeStyle, markerEnd: { type: MarkerType.ArrowClosed, color: '#E2E8F0' } },
  { id: 'e-s-ob', source: 'synthesis', target: 'output-b', style: defaultEdgeStyle, markerEnd: { type: MarkerType.ArrowClosed, color: '#E2E8F0' } },
  { id: 'e-s-oc', source: 'synthesis', target: 'output-c', style: defaultEdgeStyle, markerEnd: { type: MarkerType.ArrowClosed, color: '#E2E8F0' } },
]

export default function TaskGraph() {
  const { state, dispatch } = useDashboard()
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  const handleRun = useCallback(async () => {
    dispatch({ type: 'START_ANALYSIS' })
    try {
      await fetch('http://localhost:8000/upload-demo', { method: 'POST' })
    } catch (e) {
      console.error('Failed to start analysis:', e)
    }
  }, [dispatch])

  const buttonContent = state.systemStatus === 'idle' ? (
    <button className="run-btn" onClick={handleRun}>Run Analysis</button>
  ) : state.systemStatus === 'running' ? (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-muted)' }}>
      <div className="spinner spinner-sm" />
      Running...
    </div>
  ) : (
    <button className="run-btn run-btn--outline" onClick={handleRun}>↺ Re-run</button>
  )

  return (
    <div className="graph-col" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="panel-header" style={{ padding: '0 0 16px' }}>
        <span className="panel-header__title">TASK GRAPH</span>
        {buttonContent}
      </div>
      <div className="graph-container">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          nodesDraggable={false}
          nodesConnectable={false}
          panOnDrag={false}
          zoomOnScroll={false}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#E2E8F0" gap={20} size={1} />
        </ReactFlow>
      </div>
      <div className="graph-legend">
        <div className="graph-legend__item"><div className="graph-legend__dot" style={{ background: 'var(--text-muted)' }} /> Pending</div>
        <div className="graph-legend__item"><div className="graph-legend__dot" style={{ background: 'var(--teal)' }} /> Running</div>
        <div className="graph-legend__item"><div className="graph-legend__dot" style={{ background: 'var(--green)' }} /> Complete</div>
        <div className="graph-legend__item"><div className="graph-legend__dot" style={{ background: 'var(--red)' }} /> High Risk</div>
      </div>
    </div>
  )
}
