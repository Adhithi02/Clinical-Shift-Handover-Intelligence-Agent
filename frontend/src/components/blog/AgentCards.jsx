const agents = [
  {
    name: 'Planner Agent',
    role: 'ORCHESTRATOR',
    color: 'var(--blue)',
    bullets: [
      '→ Reads all patient PDFs via pdfplumber',
      '→ Reasons about clinical severity',
      '→ Constructs dynamic task graph per patient',
      '→ Routes to specialist agents non-deterministically',
    ],
    trigger: 'All uploads — always runs first',
  },
  {
    name: 'Risk Flag Agent',
    role: 'SAFETY MONITOR',
    color: 'var(--red)',
    bullets: [
      '→ Detects declining vital trends',
      '→ Flags post-procedure monitoring gaps',
      '→ Identifies drug interaction risks',
      '→ Returns severity: HIGH / MEDIUM / LOW',
    ],
    trigger: 'Planner detects clinical deterioration',
  },
  {
    name: 'Missing Info Agent',
    role: 'DOCUMENTATION AUDITOR',
    color: 'var(--amber)',
    bullets: [
      '→ Checks for absent post-procedure scores',
      '→ Flags incomplete medication reconciliation',
      '→ Identifies missing investigation results',
      '→ Returns completeness score + field list',
    ],
    trigger: 'Planner detects documentation gaps',
  },
  {
    name: 'Synthesis Agent',
    role: 'BRIEF WRITER',
    color: 'var(--teal)',
    bullets: [
      '→ Aggregates all agent findings',
      '→ Writes SBAR in clinical language',
      '→ Colour-codes output by severity',
      '→ Streams output live token by token',
    ],
    trigger: 'All other agents complete',
  },
]

export default function AgentCards() {
  return (
    <div className="agent-grid">
      {agents.map((a, i) => (
        <div className="agent-card" key={i} style={{ borderLeft: `4px solid ${a.color}` }}>
          <div className="agent-card__name">{a.name}</div>
          <div className="agent-card__role">{a.role}</div>
          <ul className="agent-card__bullets">
            {a.bullets.map((b, j) => <li key={j}>{b}</li>)}
          </ul>
          <div className="agent-card__trigger">Triggered by: {a.trigger}</div>
        </div>
      ))}
    </div>
  )
}
