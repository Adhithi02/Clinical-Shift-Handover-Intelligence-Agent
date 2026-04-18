import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import HeroSection from '../components/blog/HeroSection'
import StatRow from '../components/blog/StatRow'
import RoutingDiagram from '../components/blog/RoutingDiagram'
import AgentCards from '../components/blog/AgentCards'
import StackTable from '../components/blog/StackTable'
import PatientCards from '../components/blog/PatientCards'
import SbarPreview from '../components/blog/SbarPreview'
import CtaSection from '../components/blog/CtaSection'

function useScrollAnimate() {
  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible')
        }
      })
    }, { threshold: 0.1 })

    document.querySelectorAll('.scroll-animate').forEach(el => observer.observe(el))
    return () => observer.disconnect()
  }, [])
}

export default function BlogPage() {
  const navigate = useNavigate()
  useScrollAnimate()

  return (
    <>
      {/* Navbar */}
      <nav className="blog-navbar">
        <div className="blog-navbar__brand">
          <div className="pulse-dot" />
          HANDOVER.AI
        </div>
        <button className="blog-navbar__cta" onClick={() => navigate('/dashboard')}>
          Launch Dashboard →
        </button>
      </nav>

      {/* Content */}
      <div className="blog-content">
        <HeroSection />

        {/* Section 01 */}
        <section className="section scroll-animate">
          <div className="section__tag">01 — THE PROBLEM</div>
          <h2 className="section__headline">
            Shift handover is where patients fall through the cracks.
          </h2>
          <StatRow />
          <div className="section__body">
            <p>
              During hospital shift changes, the outgoing clinician verbally summarises each patient's status to the incoming team. This process is manual, inconsistent, and dangerously prone to omission — especially under time pressure at the end of a long shift.
            </p>
            <p>
              The incoming doctor has no structured record. Critical flags get buried in conversation. High-risk patients look the same as stable ones until something goes wrong.
            </p>
          </div>
        </section>

        {/* Section 02 */}
        <section className="section scroll-animate">
          <div className="section__tag">02 — THE APPROACH</div>
          <h2 className="section__headline">
            Don't build a chatbot. Build a reasoning system.
          </h2>
          <div className="section__body">
            <p>
              Most AI tools in healthcare are wrappers — you upload a document, you get a summary. The same summary, every time, regardless of what the document contains.
            </p>
            <p>
              We built something different. Our planner agent reads every patient record first, reasons about clinical severity, and constructs a different workflow for each patient. Patient B gets the Risk Flag agent. Patient A gets the Missing Info agent. Patient C goes straight to synthesis. Nothing is hardcoded.
            </p>
          </div>
          <RoutingDiagram />
        </section>

        {/* Section 03 */}
        <section className="section scroll-animate">
          <div className="section__tag">03 — ARCHITECTURE</div>
          <h2 className="section__headline">
            Four agents. One dynamic graph.
          </h2>
          <AgentCards />
          <StackTable />
        </section>

        {/* Section 04 */}
        <section className="section scroll-animate">
          <div className="section__tag">04 — DEMO DATA</div>
          <h2 className="section__headline">
            Three patients. Three traps. Three paths.
          </h2>
          <p className="section__sub">
            Each patient PDF was engineered to trigger a different agent path. Here's what the system sees.
          </p>
          <PatientCards />
        </section>

        {/* Section 05 */}
        <section className="section scroll-animate">
          <div className="section__tag">05 — OUTPUT</div>
          <h2 className="section__headline">
            SBAR in seconds. Not minutes.
          </h2>
          <div className="section__body">
            <p>
              The Synthesis Agent writes a complete, structured handover brief in SBAR format — streamed live, token by token, directly into the dashboard. Here's a preview of Patient B's output.
            </p>
          </div>
          <SbarPreview />
        </section>

        {/* Section 06 — CTA */}
        <CtaSection />

        {/* Footer */}
        <footer className="blog-footer">
          <span>Clinical Shift Handover Intelligence Agent</span>
          <span>Open source stack · Zero API cost</span>
        </footer>
      </div>
    </>
  )
}
