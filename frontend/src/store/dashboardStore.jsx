import { createContext, useContext, useReducer } from 'react'
import { DEMO_PATIENTS } from '../data/patients'

const DashboardContext = createContext()

const initialState = {
  ollamaConnected: false,
  patientsLoaded: false,
  systemStatus: 'idle',
  patients: {},
  nodeStates: {
    planner: 'pending',
    risk: 'pending',
    missing: 'pending',
    synthesis: 'pending',
    'patient-a': 'pending',
    'patient-b': 'pending',
    'patient-c': 'pending',
    'output-a': 'pending',
    'output-b': 'pending',
    'output-c': 'pending',
  },
  edgeStates: {},
  logEntries: [],
  sbarBriefs: { A: '', B: '', C: '' },
  sbarStatus: { A: 'idle', B: 'idle', C: 'idle' },
  activePatientTab: 'A',
  runtime: 0,
  progress: 0,
}

function reducer(state, action) {
  switch (action.type) {
    case 'SET_OLLAMA_STATUS':
      return { ...state, ollamaConnected: action.payload }

    case 'LOAD_PATIENTS': {
      const patients = {}
      action.payload.forEach(p => { patients[p.id] = p })
      return { ...state, patients, patientsLoaded: true }
    }

    case 'START_ANALYSIS':
      return {
        ...state,
        systemStatus: 'running',
        progress: 0,
        runtime: 0,
        logEntries: [],
        nodeStates: { ...initialState.nodeStates },
        edgeStates: {},
        sbarBriefs: { A: '', B: '', C: '' },
        sbarStatus: { A: 'idle', B: 'idle', C: 'idle' },
      }

    case 'UPDATE_NODE_STATE':
      return {
        ...state,
        nodeStates: {
          ...state.nodeStates,
          [action.payload.nodeId]: action.payload.status
        }
      }

    case 'UPDATE_EDGE_STATE':
      return {
        ...state,
        edgeStates: {
          ...state.edgeStates,
          [action.payload.edgeId]: action.payload.status
        }
      }

    case 'ADD_LOG_ENTRY':
      return {
        ...state,
        logEntries: [...state.logEntries, action.payload]
      }

    case 'APPEND_SBAR_TOKEN':
      return {
        ...state,
        sbarBriefs: {
          ...state.sbarBriefs,
          [action.payload.patient]: (state.sbarBriefs[action.payload.patient] || '') + action.payload.token
        },
        sbarStatus: {
          ...state.sbarStatus,
          [action.payload.patient]: 'generating'
        }
      }

    case 'SET_SBAR_COMPLETE':
      return {
        ...state,
        sbarBriefs: {
          ...state.sbarBriefs,
          [action.payload.patient]: action.payload.brief
        },
        sbarStatus: {
          ...state.sbarStatus,
          [action.payload.patient]: 'complete'
        },
        progress: Math.min(3, state.progress + 1)
      }

    case 'SET_ALL_COMPLETE':
      return {
        ...state,
        systemStatus: 'complete',
        progress: 3,
        sbarStatus: { A: 'complete', B: 'complete', C: 'complete' }
      }

    case 'SET_ACTIVE_TAB':
      return { ...state, activePatientTab: action.payload }

    case 'TRIGGER_REPLAN':
      return {
        ...state,
        systemStatus: 'running',
        sbarStatus: {
          ...state.sbarStatus,
          [action.payload]: 'generating'
        },
        sbarBriefs: {
          ...state.sbarBriefs,
          [action.payload]: ''
        }
      }

    case 'CANCEL_REPLAN':
      return {
        ...state,
        systemStatus: 'idle',
        sbarStatus: {
          ...state.sbarStatus,
          [action.payload]: 'idle' // or 'error', or we could cache the old brief. 'idle' is fine.
        }
      }

    case 'TICK_RUNTIME':
      return { ...state, runtime: state.runtime + 1 }

    case 'SET_SYSTEM_STATUS':
      return { ...state, systemStatus: action.payload }

    default:
      return state
  }
}

export function DashboardProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  return (
    <DashboardContext.Provider value={{ state, dispatch }}>
      {children}
    </DashboardContext.Provider>
  )
}

export function useDashboard() {
  const ctx = useContext(DashboardContext)
  if (!ctx) throw new Error('useDashboard must be within DashboardProvider')
  return ctx
}
