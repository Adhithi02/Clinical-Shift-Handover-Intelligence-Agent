import { useDashboard } from '../../store/dashboardStore'
import DoctorOverride from './DoctorOverride'

const PATIENT_TABS = [
  { id: 'A', label: 'Patient A', color: 'amber' },
  { id: 'B', label: 'Patient B', color: 'red' },
  { id: 'C', label: 'Patient C', color: 'green' },
]

const PATIENT_META = {
  A: { name: 'Arun Mehta', age: 58, severity: 'MEDIUM', severityLabel: '● MEDIUM RISK' },
  B: { name: 'Priya Sharma', age: 71, severity: 'HIGH', severityLabel: '● HIGH RISK' },
  C: { name: 'Ravi Kumar', age: 45, severity: 'LOW', severityLabel: '● STABLE' },
}

const SEVERITY_COLORS = {
  HIGH: 'var(--red)',
  MEDIUM: 'var(--amber)',
  LOW: 'var(--green)',
}

const SEVERITY_DIMS = {
  HIGH: 'var(--red-dim)',
  MEDIUM: 'var(--amber-dim)',
  LOW: 'var(--green-dim)',
}

const SBAR_LETTERS = {
  S: { color: 'var(--blue)', label: 'Situation' },
  B: { color: 'var(--text-muted)', label: 'Background' },
  A: { color: null, label: 'Assessment' },
  R: { color: 'var(--teal)', label: 'Recommendation' },
}

function parseSbar(brief) {
  if (!brief) return null
  if (typeof brief === 'object' && brief.sbar) {
    const sbar = brief.sbar
    return {
      severity: brief.severity || brief.color || 'LOW',
      sections: {
        S: sbar.situation || sbar.S || '',
        B: sbar.background || sbar.B || '',
        A: sbar.assessment || sbar.A || '',
        R: sbar.recommendation || sbar.R || '',
      }
    }
  }
  if (typeof brief === 'string') {
    const sections = { S: '', B: '', A: '', R: '' }
    const parts = brief.split(/\n(?=[SBAR]:)/i)
    parts.forEach(p => {
      if (p.startsWith('S:')) sections.S = p.slice(2).trim()
      else if (p.startsWith('B:')) sections.B = p.slice(2).trim()
      else if (p.startsWith('A:')) sections.A = p.slice(2).trim()
      else if (p.startsWith('R:')) sections.R = p.slice(2).trim()
    })
    if (!sections.S && !sections.B) sections.S = brief
    return { severity: 'LOW', sections }
  }
  return null
}

export default function SbarPanel() {
  const { state, dispatch } = useDashboard()
  const activeTab = state.activePatientTab
  const sbarStatus = state.sbarStatus[activeTab]
  const brief = state.sbarBriefs[activeTab]
  const meta = PATIENT_META[activeTab]
  const parsed = parseSbar(brief)
  const severity = parsed?.severity || meta.severity
  const sevColor = SEVERITY_COLORS[severity] || SEVERITY_COLORS.LOW
  const sevDim = SEVERITY_DIMS[severity] || SEVERITY_DIMS.LOW

  return (
    <div className="dashboard__col">
      <div className="panel-header" style={{ paddingBottom: 0 }}>
        <span className="panel-header__title">SBAR BRIEF</span>
      </div>
      <div className="sbar-tabs-dash">
        {PATIENT_TABS.map(t => {
          const isActive = activeTab === t.id
          return (
            <button
              key={t.id}
              className={`sbar-tab-dash ${isActive ? `sbar-tab-dash--active sbar-tab-dash--active-${t.color}` : ''}`}
              onClick={() => dispatch({ type: 'SET_ACTIVE_TAB', payload: t.id })}
            >{t.label}</button>
          )
        })}
      </div>

      <div className="sbar-content-area">
        {sbarStatus === 'idle' && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
            Run analysis to generate SBAR briefs
          </div>
        )}

        {sbarStatus === 'generating' && (
          <>
            <div className="generating-badge">GENERATING...<span className="cursor-blink">|</span></div>
            <div className="shimmer-line" />
            <div className="shimmer-line" />
            <div className="shimmer-line" />
            <div className="shimmer-line" />
          </>
        )}

        {sbarStatus === 'complete' && parsed && (
          <div className="sbar-card-dash">
            <div className="sbar-card-dash__header" style={{ background: sevColor }}>
              <span className="sbar-card-dash__badge">{meta.severityLabel}</span>
              <span className="sbar-card-dash__name">{meta.name}, {meta.age}</span>
            </div>
            <div className="sbar-card-dash__sections">
              {['S', 'B', 'A', 'R'].map(letter => {
                const letterColor = letter === 'A' ? sevColor : SBAR_LETTERS[letter].color
                const content = parsed.sections[letter] || ''
                return (
                  <div className="sbar-card-section" key={letter}>
                    <div className="sbar-card-section__letter" style={{ color: letterColor }}>{letter}</div>
                    <div>
                      <div className="sbar-card-section__label">{SBAR_LETTERS[letter].label}</div>
                      <div className="sbar-card-section__content">
                        {letter === 'R' ? (
                          content.split(/\d+\.\s*|→\s*/).filter(Boolean).map((item, i) => (
                            <div className="rec-item" key={i}>
                              <span className="rec-arrow">→</span>
                              <span style={{ fontWeight: 500 }}>{item.trim()}</span>
                            </div>
                          ))
                        ) : content}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      <DoctorOverride />
    </div>
  )
}
