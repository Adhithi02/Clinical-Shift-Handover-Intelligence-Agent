import { useNavigate } from 'react-router-dom'

export default function CtaSection() {
  const navigate = useNavigate()

  return (
    <section className="cta-section scroll-animate">
      <h2 className="cta-section__headline">See it run live.</h2>
      <p className="cta-section__sub">Real agents. Real LLM. Real-time replanning.</p>
      <button className="cta-section__btn" onClick={() => navigate('/dashboard')}>
        → Launch Agent Dashboard
      </button>
      <div className="cta-section__note">Runs locally · Zero API cost · Ollama + LangGraph</div>
    </section>
  )
}
