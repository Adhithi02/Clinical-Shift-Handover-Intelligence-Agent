export default function SbarPreview() {
  return (
    <div className="sbar-preview">
      <div className="sbar-preview__header">
        <span className="sbar-preview__badge">● HIGH RISK</span>
        <span className="sbar-preview__name">PATIENT B — Priya Sharma, 71</span>
      </div>
      <div className="sbar-preview__body">
        <div className="sbar-section-preview">
          <div className="sbar-letter" style={{ color: 'var(--blue)' }}>S</div>
          <div>
            <div className="sbar-section-preview__label">Situation</div>
            <div className="sbar-section-preview__content">
              71F admitted with chest pain (query ACS).
              Systolic BP declining over 6 hours
              (<span className="highlight-red">138→131→122→114 mmHg</span>).
              Currently haemodynamically borderline. Troponin result pending.
            </div>
          </div>
        </div>

        <div className="sbar-section-preview">
          <div className="sbar-letter" style={{ color: 'var(--text-muted)' }}>B</div>
          <div>
            <div className="sbar-section-preview__label">Background</div>
            <div className="sbar-section-preview__content">
              Previous cardiac history unknown. On Aspirin 300mg,
              GTN PRN, Metoprolol 25mg BD. ECG on admission: sinus
              rhythm, no acute ST changes. Chest pain onset 6 hours
              prior to admission.
            </div>
          </div>
        </div>

        <div className="sbar-section-preview">
          <div className="sbar-letter" style={{ color: 'var(--red)' }}>A</div>
          <div>
            <div className="sbar-section-preview__label">Assessment</div>
            <div className="sbar-section-preview__content">
              <span className="highlight-red">HIGH RISK</span>. Persistent BP decline without clear cause.
              Troponin result outstanding — <span className="highlight-red">ACS not yet excluded</span>.
            </div>
          </div>
        </div>

        <div className="sbar-section-preview">
          <div className="sbar-letter" style={{ color: 'var(--teal)' }}>R</div>
          <div>
            <div className="sbar-section-preview__label">Recommendation</div>
            <div className="sbar-section-preview__content">
              <div className="rec-item"><span className="rec-arrow">→</span> 1. Obtain troponin result immediately.</div>
              <div className="rec-item"><span className="rec-arrow">→</span> 2. Repeat 12-lead ECG and compare to admission.</div>
              <div className="rec-item"><span className="rec-arrow">→</span> 3. Senior review within 30 minutes.</div>
              <div className="rec-item"><span className="rec-arrow">→</span> 4. Prepare for potential escalation to CCU.</div>
              <div className="rec-item"><span className="rec-arrow">→</span> 5. Do not discharge — monitor hourly BP.</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
