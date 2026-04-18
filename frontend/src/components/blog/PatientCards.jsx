import { useEffect, useRef, useState } from 'react'
import { DEMO_PATIENTS } from '../../data/patients'

function BpChart({ vitals }) {
  const [animated, setAnimated] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) setAnimated(true)
    }, { threshold: 0.3 })
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])

  const systolics = vitals.map(v => parseInt(v.value.split('/')[0]))
  const maxVal = 150
  const colors = ['var(--green)', 'var(--green)', 'var(--amber)', 'var(--red)']

  return (
    <div className="bp-chart" ref={ref}>
      {systolics.map((val, i) => (
        <div className="bp-bar-wrap" key={i}>
          <div
            className="bp-bar"
            style={{
              height: animated ? `${(val / maxVal) * 44}px` : '0px',
              background: colors[i],
              transitionDelay: `${i * 100}ms`,
            }}
          />
          <span className="bp-bar-label">{val}</span>
        </div>
      ))}
    </div>
  )
}

export default function PatientCards() {
  return (
    <div className="patient-cards-blog">
      {DEMO_PATIENTS.map((p) => {
        const alertClass = p.alert.type === 'danger' ? 'alert-box--danger'
          : p.alert.type === 'warning' ? 'alert-box--warning' : 'alert-box--success'
        const alertIcon = p.alert.type === 'danger' ? '●' : p.alert.type === 'warning' ? '⚠' : '✓'
        const badgeClass = `condition-badge--${p.conditionColor}`

        return (
          <div className="patient-card-blog" key={p.id}>
            <div className="patient-card-blog__header">
              <div>
                <div className="patient-card-blog__name">{p.name}</div>
                <div className="patient-card-blog__age">Age {p.age} · {p.condition}</div>
              </div>
              <div className={`condition-badge ${badgeClass}`}>{p.condition}</div>
            </div>

            {p.id === 'B' ? (
              <BpChart vitals={p.vitals} />
            ) : (
              <div className="vitals-grid">
                {p.vitals.map((v, i) => (
                  <div className="vital-cell" key={i}>
                    <div className="vital-cell__label">{v.label}</div>
                    <div className="vital-cell__value">{v.value}</div>
                    <div className={`vital-cell__dot vital-cell__dot--${v.status}`} />
                  </div>
                ))}
              </div>
            )}

            <div className={`alert-box ${alertClass}`}>
              {alertIcon} {p.alert.text}
            </div>
          </div>
        )
      })}
    </div>
  )
}
