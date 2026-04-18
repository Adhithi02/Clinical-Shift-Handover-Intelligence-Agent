import { useNavigate } from 'react-router-dom'

export default function HeroSection() {
  const navigate = useNavigate()

  return (
    <section className="hero scroll-animate visible">
      <div className="hero__tag">[ CLINICAL AI · AGENTIC HANDOVER SYSTEM ]</div>
      <h1 className="hero__headline">
        The AI That Reads<br />
        Your Patients<br />
        Before You Do.
      </h1>
      <p className="hero__sub">
        How we built a zero-cost agentic handover system using LangGraph, Ollama, and A2A protocol — with real-time replanning and human-in-the-loop control.
      </p>
    </section>
  )
}
