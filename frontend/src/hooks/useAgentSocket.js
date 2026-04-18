import { useEffect, useRef } from 'react'

export function useAgentSocket(dispatch) {
  const wsRef = useRef(null)

  useEffect(() => {
    let retryTimeout

    function connect() {
      const ws = new WebSocket('ws://localhost:8000/ws')
      wsRef.current = ws

      ws.onopen = () => {
        dispatch({ type: 'SET_SYSTEM_STATUS', payload: 'connected' })
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          if (msg.type === 'connection' || msg.type === 'pong') return

          // Add log entry
          if (msg.agent && msg.message) {
            dispatch({ type: 'ADD_LOG_ENTRY', payload: {
              id: Date.now() + Math.random(),
              timestamp: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
              agent: (msg.agent || '').toUpperCase(),
              message: msg.message,
              status: msg.status
            }})
          }

          // Map agent names to node IDs
          const agentNodeMap = {
            planner: 'planner',
            risk: 'risk',
            missing: 'missing',
            synthesis: 'synthesis',
            orchestrator: null
          }
          const nodeId = agentNodeMap[msg.agent]
          if (nodeId) {
            dispatch({ type: 'UPDATE_NODE_STATE', payload: { nodeId, status: msg.status } })
          }

          // Map patient routing to patient nodes
          if (msg.agent === 'planner' && msg.status === 'complete' && msg.patient && msg.patient !== 'all') {
            const patientLetter = msg.patient.match(/PAT-([A-Z])/i)?.[1] || msg.patient
            dispatch({ type: 'UPDATE_NODE_STATE', payload: {
              nodeId: `patient-${patientLetter.toLowerCase()}`,
              status: 'complete'
            }})
          }

          // Handle SBAR streaming tokens
          if (msg.agent === 'synthesis' && msg.token) {
            const patientLetter = msg.patient?.match(/PAT-([A-Z])/i)?.[1] || msg.patient
            dispatch({ type: 'APPEND_SBAR_TOKEN', payload: { patient: patientLetter, token: msg.token } })
          }

          // Handle SBAR completion
          if (msg.agent === 'synthesis' && msg.status === 'complete' && msg.result) {
            const patientLetter = msg.patient?.match(/PAT-([A-Z])/i)?.[1] || msg.patient
            dispatch({ type: 'SET_SBAR_COMPLETE', payload: {
              patient: patientLetter,
              brief: msg.result
            }})
            dispatch({ type: 'UPDATE_NODE_STATE', payload: {
              nodeId: `output-${patientLetter.toLowerCase()}`,
              status: 'complete'
            }})
          }

          // Handle workflow complete
          if (msg.type === 'workflow_status' && msg.status === 'complete') {
            dispatch({ type: 'SET_ALL_COMPLETE' })
          }
        } catch (e) {
          // Ignore parse errors
        }
      }

      ws.onclose = () => {
        retryTimeout = setTimeout(connect, 3000)
      }
      ws.onerror = () => ws.close()
    }

    connect()
    return () => {
      clearTimeout(retryTimeout)
      wsRef.current?.close()
    }
  }, [dispatch])
}
