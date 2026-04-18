const rows = [
  { layer: 'LLM',           tool: 'Ollama + Llama 3.2', cost: 'FREE' },
  { layer: 'Orchestration',  tool: 'LangGraph (Python)',  cost: 'FREE' },
  { layer: 'Agent Comms',    tool: 'python-a2a',          cost: 'FREE' },
  { layer: 'Tool Exposure',  tool: 'FastMCP',             cost: 'FREE' },
  { layer: 'PDF Extraction', tool: 'pdfplumber',          cost: 'FREE' },
  { layer: 'Backend',        tool: 'FastAPI + WebSockets', cost: 'FREE' },
  { layer: 'Frontend',       tool: 'React + React Flow',  cost: 'FREE' },
]

export default function StackTable() {
  return (
    <div className="stack-table">
      <div className="stack-table__header">
        <span>LAYER</span>
        <span>TOOL</span>
        <span>COST</span>
      </div>
      {rows.map((r, i) => (
        <div className="stack-table__row" key={i}>
          <span className="stack-table__layer">{r.layer}</span>
          <span className="stack-table__tool">{r.tool}</span>
          <span><span className="stack-table__cost">{r.cost}</span></span>
        </div>
      ))}
    </div>
  )
}
