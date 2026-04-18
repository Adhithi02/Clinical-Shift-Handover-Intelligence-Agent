export default function RoutingDiagram() {
  const routes = [
    { name: 'Patient A', sub: 'Post-Surgery', color: 'var(--amber)', badge: 'Missing Info Agent', badgeBg: 'var(--amber-dim)', badgeColor: 'var(--amber)' },
    { name: 'Patient B', sub: 'Cardiac Monitoring', color: 'var(--red)', badge: 'Risk Flag Agent', badgeBg: 'var(--red-dim)', badgeColor: 'var(--red)' },
    { name: 'Patient C', sub: 'UTI — Stable', color: 'var(--green)', badge: 'Synthesis Agent', badgeBg: 'var(--green-dim)', badgeColor: 'var(--green)' },
  ]

  return (
    <div className="routing-diagram">
      {routes.map((r, i) => (
        <div className="routing-row" key={i}>
          <div className="routing-patient">
            <div className="routing-patient__bar" style={{ background: r.color }} />
            <div>
              <div className="routing-patient__name">{r.name}</div>
              <div className="routing-patient__sub">{r.sub}</div>
            </div>
          </div>
          <div className="routing-line" style={{ color: r.color }} />
          <div className="routing-badge" style={{ background: r.badgeBg, color: r.badgeColor }}>
            {r.badge}
          </div>
        </div>
      ))}
    </div>
  )
}
