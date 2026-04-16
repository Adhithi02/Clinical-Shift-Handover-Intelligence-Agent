import { useState } from 'react'

function SbarPanel({ sbarResults, onFeedback, workflowStatus }) {
  const [activeTab, setActiveTab] = useState(null)
  const [feedbackText, setFeedbackText] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const patients = Object.entries(sbarResults || {})

  if (patients.length > 0 && !activeTab) {
    setTimeout(() => setActiveTab(patients[0][0]), 0)
  }

  const handleSubmitFeedback = async () => {
    if (!feedbackText.trim() || !activeTab) return
    setSubmitting(true)
    try {
      await onFeedback(activeTab, feedbackText)
      setFeedbackText('')
    } catch (err) {
      console.error('Feedback error:', err)
    }
    setSubmitting(false)
  }

  if (patients.length === 0) {
    return (
      <div className="panel-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '13px', fontWeight: 500 }}>No SBAR briefs yet</div>
        </div>
      </div>
    )
  }

  const activeSbar = sbarResults[activeTab]
  const sbar = activeSbar?.sbar || {}
  const color = activeSbar?.color || 'GREEN'
  const patientName = activeSbar?.patient_name || activeTab

  return (
    <>
      <div className="sbar-tabs">
        {patients.map(([patientId, result]) => {
          const patientColor = result?.color || 'GREEN'
          const shortId = patientId.match(/PAT-([A-Z])/i)
          const label = shortId ? `Patient ${shortId[1]}` : patientId
          
          return (
            <button
              key={patientId}
              className={`sbar-tab ${activeTab === patientId ? 'active' : ''}`}
              onClick={() => setActiveTab(patientId)}
            >
              <span style={{ 
                display: 'inline-block', 
                width: 8, height: 8, borderRadius: '50%', 
                backgroundColor: `var(--color-${patientColor === 'RED' ? 'high' : patientColor === 'AMBER' ? 'med' : 'low'}-border)`,
                marginRight: 6
              }}></span>
              {label}
            </button>
          )
        })}
      </div>

      <div className="panel-body sbar-container">
        {activeSbar && (
          <>
            <div className={`sbar-header ${color}`}>
              <div>
                <div className="sbar-name">{patientName}</div>
                <div style={{ fontSize: '12px', marginTop: '2px', opacity: 0.8 }}>ID: {activeTab}</div>
              </div>
              <div className="sbar-badge">
                {color === 'RED' ? 'HIGH RISK' : color === 'AMBER' ? 'MED RISK' : 'STABLE'}
              </div>
            </div>

            {activeSbar.replanned && (
              <div style={{ padding: '8px', background: 'var(--color-info-bg)', borderRadius: '6px', fontSize: '12px', border: '1px solid var(--color-info-border)', color: 'var(--color-info-text)' }}>
                <strong>Updated via Doctor Feedback:</strong><br/>
                <span style={{ fontStyle: 'italic' }}>"{activeSbar.doctor_feedback}"</span>
              </div>
            )}

            <div className="sbar-section">
              <span className="sbar-title">Situation</span>
              <span className="sbar-body">{sbar.situation || 'Not available'}</span>
            </div>

            <div className="sbar-section">
              <span className="sbar-title">Background</span>
              <span className="sbar-body">{sbar.background || 'Not available'}</span>
            </div>

            <div className="sbar-section">
              <span className="sbar-title">Assessment</span>
              <span className="sbar-body" style={{ fontWeight: color !== 'GREEN' ? 600 : 400 }}>
                {sbar.assessment || 'Not available'}
              </span>
            </div>

            <div className="sbar-section">
              <span className="sbar-title">Recommendation</span>
              <span className="sbar-body" style={{ fontWeight: 600 }}>
                {sbar.recommendation || 'Not available'}
              </span>
            </div>

            <div className="sbar-footer">
              <div className="feedback-label">Doctor Feedback / Intervene</div>
              <textarea
                className="feedback-input"
                placeholder="Submit feedback to adjust evaluation or correct risk..."
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                disabled={submitting || workflowStatus === 'replanning'}
              />
              <div className="footer-actions">
                <button
                  className="btn btn-primary"
                  onClick={handleSubmitFeedback}
                  disabled={!feedbackText.trim() || submitting || workflowStatus === 'replanning'}
                >
                  {workflowStatus === 'replanning' ? 'Replanning...' : 'Submit Feedback & Replan'}
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  )
}

export default SbarPanel
