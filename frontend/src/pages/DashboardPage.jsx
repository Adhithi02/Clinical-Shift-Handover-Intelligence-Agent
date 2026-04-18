import { useEffect, useState } from 'react'
import { DashboardProvider, useDashboard } from '../store/dashboardStore'
import { useAgentSocket } from '../hooks/useAgentSocket'
import { checkOllama } from '../utils/ollama'
import { DEMO_PATIENTS } from '../data/patients'
import TopBar from '../components/dashboard/TopBar'
import TaskGraph from '../components/dashboard/TaskGraph'
import MessageFeed from '../components/dashboard/MessageFeed'
import SbarPanel from '../components/dashboard/SbarPanel'
import StatusBar from '../components/dashboard/StatusBar'
import UploadOverlay from '../components/dashboard/UploadOverlay'

function DashboardInner() {
  const { state, dispatch } = useDashboard()
  const [ollamaBanner, setOllamaBanner] = useState(false)
  const [showUpload, setShowUpload] = useState(false)

  // Connect WebSocket
  useAgentSocket(dispatch)

  // Health checks on mount
  useEffect(() => {
    // Check Ollama
    checkOllama().then(ok => {
      dispatch({ type: 'SET_OLLAMA_STATUS', payload: ok })
      if (!ok) setOllamaBanner(true)
    })

    // Check backend health
    fetch('http://localhost:8000/')
      .then(r => r.json())
      .then(() => {})
      .catch(() => {})

    // Load demo patients
    dispatch({ type: 'LOAD_PATIENTS', payload: DEMO_PATIENTS })
  }, [dispatch])

  const handleUpload = async (files) => {
    setShowUpload(false)
    if (!files || files.length === 0) return

    const formData = new FormData()
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i])
    }

    dispatch({ type: 'START_ANALYSIS' })
    try {
      await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData
      })
    } catch (err) {
      console.error('Upload failed:', err)
    }
  }

  return (
    <div className="dashboard">
      <TopBar onUploadClick={() => setShowUpload(true)} />
      
      <UploadOverlay 
        show={showUpload} 
        onClose={() => setShowUpload(false)} 
        onUpload={handleUpload} 
      />

      {ollamaBanner && (
        <div className="alert-banner">
          <span>⚠ Ollama not detected at localhost:11434 — Start with: OLLAMA_ORIGINS=* ollama serve</span>
          <button className="alert-banner__dismiss" onClick={() => setOllamaBanner(false)}>×</button>
        </div>
      )}

      <div className="dashboard__main">
        {/* Column 1: Task Graph */}
        <div className="dashboard__col">
          <TaskGraph />
        </div>

        {/* Column 2: Message Feed */}
        <MessageFeed />

        {/* Column 3: SBAR Panel */}
        <SbarPanel />
      </div>

      <StatusBar />
    </div>
  )
}

export default function DashboardPage() {
  return (
    <DashboardProvider>
      <DashboardInner />
    </DashboardProvider>
  )
}
