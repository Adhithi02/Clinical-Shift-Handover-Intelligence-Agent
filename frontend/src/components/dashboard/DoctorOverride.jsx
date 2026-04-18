import { useState } from 'react'
import { useDashboard } from '../../store/dashboardStore'

export default function DoctorOverride() {
  const { state, dispatch } = useDashboard()
  const [text, setText] = useState('')
  const [replanning, setReplanning] = useState(false)
  const activeTab = state.activePatientTab

  const handleReplan = async () => {
    if (!text.trim()) return
    setReplanning(true)

    dispatch({ type: 'TRIGGER_REPLAN', payload: activeTab })
    dispatch({ type: 'ADD_LOG_ENTRY', payload: {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      agent: 'SYSTEM',
      message: `Replan triggered for Patient ${activeTab}`,
      status: 'running'
    }})
    dispatch({ type: 'ADD_LOG_ENTRY', payload: {
      id: Date.now() + 1,
      timestamp: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      agent: 'PLANNER',
      message: 'Incorporating doctor context...',
      status: 'running'
    }})

    try {
      const patientIdMap = {
        A: 'PAT-A-2024-0891',
        B: 'PAT-B-2024-0892',
        C: 'PAT-C-2024-0893',
      }
      const res = await fetch('http://localhost:8000/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: patientIdMap[activeTab] || activeTab,
          instruction: text,
        })
      })
      if (!res.ok) {
        throw new Error(await res.text())
      }
      
      const data = await res.json()
      if (data && data.new_sbar) {
        dispatch({ type: 'SET_SBAR_COMPLETE', payload: {
          patient: activeTab,
          brief: data.new_sbar
        }})
      }
    } catch (e) {
      console.error('Replan failed:', e)
      dispatch({ type: 'CANCEL_REPLAN', payload: activeTab })
      dispatch({ type: 'ADD_LOG_ENTRY', payload: {
        id: Date.now() + 2,
        timestamp: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        agent: 'SYSTEM',
        message: 'Replan failed. Check if patient ID matches or see backend logs.',
        status: 'error'
      }})
    }

    setText('')
    setReplanning(false)
  }

  return (
    <div className="doctor-override">
      <div className="doctor-override__label">DOCTOR OVERRIDE</div>
      <textarea
        className="doctor-override__textarea"
        rows={3}
        placeholder="e.g. Patient B has naturally low BP, reconsider risk level..."
        value={text}
        onChange={e => setText(e.target.value)}
        disabled={replanning}
      />
      <button
        className={`doctor-override__btn ${replanning ? 'doctor-override__btn--replanning' : ''}`}
        onClick={handleReplan}
        disabled={replanning || !text.trim()}
      >
        {replanning ? '↺ Replanning...' : '↺ Replan with this context'}
      </button>
    </div>
  )
}
