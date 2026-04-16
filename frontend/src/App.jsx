import { useState, useEffect, useRef, useCallback } from 'react'
import TaskGraph from './components/TaskGraph'
import MessageFeed from './components/MessageFeed'
import SbarPanel from './components/SbarPanel'
import axios from 'axios'

const API_URL = 'http://localhost:8000'
const WS_URL = 'ws://localhost:8000/ws'

function App() {
  const [messages, setMessages] = useState([])
  const [sbarResults, setSbarResults] = useState({})
  const [taskGraph, setTaskGraph] = useState([])
  const [nodeStates, setNodeStates] = useState({})
  const [workflowStatus, setWorkflowStatus] = useState('idle')
  const [mode, setMode] = useState('simulation')
  const [showUpload, setShowUpload] = useState(false)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const fileInputRef = useRef(null)
  const reconnectTimerRef = useRef(null)

  // WebSocket connection
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(WS_URL)
    
    ws.onopen = () => {
      setConnected(true)
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.type === 'connection') {
          setWorkflowStatus(data.workflow_status || 'idle')
          setMode(data.mode || 'simulation')
          return
        }

        if (data.type === 'pong') return

        // Add to messages
        setMessages(prev => [...prev, data])

        // Update node states for task graph
        if (data.agent && data.patient && data.status) {
          const nodeId = `${data.agent}-${data.patient}`
          setNodeStates(prev => ({
            ...prev,
            [nodeId]: {
              agent: data.agent,
              patient: data.patient,
              status: data.status,
              message: data.message || '',
              result: data.result || null
            }
          }))
        }

        // Update workflow status
        if (data.type === 'workflow_status') {
          setWorkflowStatus(data.status)
        }
        
        if (data.type === 'replan_status') {
          setWorkflowStatus(data.status === 'complete' ? 'complete' : 'replanning')
        }

        // Update task graph routing info
        if (data.agent === 'planner' && data.status === 'complete' && data.result?.route) {
          const rawAgentsForState = data.result.agents_to_invoke || data.result.agents || []
          const agentsArray = Array.isArray(rawAgentsForState) 
            ? rawAgentsForState 
            : (typeof rawAgentsForState === 'string' ? rawAgentsForState.split(/[|,]/) : [rawAgentsForState])

          setTaskGraph(prev => {
            const existing = prev.find(t => t.patient_id === data.patient)
            if (existing) {
              return prev.map(t => t.patient_id === data.patient 
                ? { ...t, route: data.result.route, agents: agentsArray } 
                : t)
            }
            return [...prev, { 
              patient_id: data.patient, 
              name: data.patient_name || data.patient,
              route: data.result.route, 
              priority: data.result.priority,
              agents: agentsArray
            }]
          })
        }

        // Update SBAR results (Merge existing to avoid losing flags like 'replanned')
        if (data.agent === 'synthesis' && data.status === 'complete' && data.result?.sbar) {
          setSbarResults(prev => ({
            ...prev,
            [data.patient]: {
              ...(prev[data.patient] || {}), // Preserve existing state
              ...data.result,               // Merge new results (color, severity, sbar, replanned, etc.)
              patient_id: data.patient,
              patient_name: data.result.patient_name || data.patient_name || (prev[data.patient]?.patient_name) || data.patient
            }
          }))
        }

      } catch (e) {
        console.warn('Failed to parse WebSocket message:', e)
      }
    }

    ws.onclose = () => {
      setConnected(false)
      console.log('WebSocket disconnected, reconnecting...')
      reconnectTimerRef.current = setTimeout(connectWebSocket, 3000)
    }

    ws.onerror = () => {
      setConnected(false)
    }

    wsRef.current = ws
  }, [])

  useEffect(() => {
    connectWebSocket()
    return () => {
      if (wsRef.current) wsRef.current.close()
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
    }
  }, [connectWebSocket])

  // Ping to keep alive
  useEffect(() => {
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping')
      }
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  // Load demo data
  const handleLoadDemo = async () => {
    try {
      setWorkflowStatus('running')
      setMessages([])
      setNodeStates({})
      setTaskGraph([])
      setSbarResults({})
      await axios.post(`${API_URL}/upload-demo`)
    } catch (err) {
      console.error('Demo load failed:', err)
      setWorkflowStatus('error')
    }
  }

  // Upload PDFs
  const handleUpload = async (files) => {
    if (!files || files.length === 0) return
    
    const formData = new FormData()
    for (const file of files) {
      formData.append('files', file)
    }
    
    try {
      setShowUpload(false)
      setWorkflowStatus('running')
      setMessages([])
      setNodeStates({})
      setTaskGraph([])
      setSbarResults({})
      await axios.post(`${API_URL}/upload`, formData)
    } catch (err) {
      console.error('Upload failed:', err)
      setWorkflowStatus('error')
    }
  }

  // Replan feedback
  const handleFeedback = async (patientId, instruction) => {
    try {
      setWorkflowStatus('replanning')
      
      // Reset affected node states
      Object.keys(nodeStates).forEach(key => {
        if (key.includes(patientId)) {
          setNodeStates(prev => ({
            ...prev,
            [key]: { ...prev[key], status: 'pending' }
          }))
        }
      })

      const response = await axios.post(`${API_URL}/feedback`, {
        patient_id: patientId,
        instruction: instruction
      })

      if (response.data.new_sbar) {
        setSbarResults(prev => ({
          ...prev,
          [patientId]: response.data.new_sbar
        }))
      }

      // Fetch full updated results
      const resultsRes = await axios.get(`${API_URL}/results`)
      if (resultsRes.data.sbar_results) {
        setSbarResults(resultsRes.data.sbar_results)
      }

      setWorkflowStatus('complete')
    } catch (err) {
      console.error('Feedback failed:', err)
      setWorkflowStatus('error')
    }
  }

  // Fetch results if page loads after workflow complete
  useEffect(() => {
    const fetchExisting = async () => {
      try {
        const res = await axios.get(`${API_URL}/results`)
        if (res.data.sbar_results && Object.keys(res.data.sbar_results).length > 0) {
          setSbarResults(res.data.sbar_results)
          setTaskGraph(res.data.task_graph || [])
          setWorkflowStatus(res.data.workflow_status)
          setMode(res.data.mode)
        }
      } catch (e) {
        // Backend not running yet
      }
    }
    fetchExisting()
  }, [])

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-title">
          Clinical Shift Handover Intelligence
        </div>
        <div className={`status-indicator ${workflowStatus}`}>
          <div className="status-dot"></div>
          {workflowStatus === 'idle' ? 'System Ready' : 
           workflowStatus === 'running' ? 'Processing Handover...' : 
           workflowStatus === 'replanning' ? 'Replanning...' : 'Complete'}
        </div>
        <div className="header-actions">
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            <strong>{Object.keys(sbarResults).length}</strong> Patients
          </div>
          <button 
            className="btn btn-outline" 
            onClick={() => setShowUpload(true)}
            disabled={workflowStatus === 'running'}
          >
            Upload PDFs
          </button>
          <button 
            className="btn btn-primary" 
            onClick={handleLoadDemo}
            disabled={workflowStatus === 'running'}
          >
            Load Demo
          </button>
        </div>
      </header>

      {/* Upload Modal */}
      {showUpload && (
        <div className="upload-overlay" onClick={() => setShowUpload(false)}>
          <div className="upload-box" 
            onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click() }}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { 
              e.preventDefault()
              handleUpload(e.dataTransfer.files)
            }}
          >
            <div style={{ fontWeight: 600, fontSize: '15px' }}>Drop patient PDFs here</div>
            <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '8px' }}>Supports multiple files</div>
            <input 
              ref={fileInputRef}
              type="file" 
              style={{ display: 'none' }} 
              multiple 
              accept=".pdf"
              onChange={(e) => handleUpload(e.target.files)}
            />
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="main-content">
        {/* Panel 1: Agent Message Feed */}
        <div className="panel">
          <div className="panel-header">
            <span>Agent Feed</span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 'normal' }}>
              {messages.length} updates
            </span>
          </div>
          <div className="panel-body">
            <MessageFeed messages={messages} />
          </div>
        </div>

        {/* Panel 2: Live Task Graph */}
        <div className="panel panel-graph">
          <div className="panel-header">
            <span>Live Task Graph</span>
            <div className="status-indicator" style={{ gap: '4px' }}>
              <div className={`status-dot`} style={{ background: connected ? 'var(--color-low-border)' : 'var(--color-med-border)' }}></div>
              <span style={{ fontSize: '11px', fontWeight: 'normal' }}>{connected ? 'Connected' : 'Disconnected'}</span>
            </div>
          </div>
          <div className="panel-body">
            <TaskGraph 
              taskGraph={taskGraph} 
              nodeStates={nodeStates}
              workflowStatus={workflowStatus}
            />
          </div>
        </div>

        {/* Panel 3: SBAR Brief Output */}
        <div className="panel">
          <div className="panel-header">
            <span>SBAR Brief Output</span>
          </div>
          {/* Panel body and footer are handled internally by SbarPanel */}
          <SbarPanel 
            sbarResults={sbarResults}
            onFeedback={handleFeedback}
            workflowStatus={workflowStatus}
          />
        </div>
      </main>
    </div>
  )
}

export default App
