import { useEffect, useRef, useState } from 'react'

function AnimatedNumber({ target, suffix = '', duration = 1500 }) {
  const [value, setValue] = useState(0)
  const ref = useRef(null)
  const started = useRef(false)

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting && !started.current) {
        started.current = true
        const start = performance.now()
        function tick(now) {
          const elapsed = now - start
          const progress = Math.min(elapsed / duration, 1)
          const eased = 1 - Math.pow(1 - progress, 3)
          setValue(Math.round(target * eased))
          if (progress < 1) requestAnimationFrame(tick)
        }
        requestAnimationFrame(tick)
      }
    }, { threshold: 0.3 })
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [target, duration])

  return <span ref={ref}>{value}{suffix}</span>
}

export default function StatRow() {
  return (
    <div className="stat-row">
      <div className="stat-card">
        <div className="stat-card__number"><AnimatedNumber target={80} suffix="%" /></div>
        <div className="stat-card__label">of adverse events involve communication failure at handover</div>
      </div>
      <div className="stat-card">
        <div className="stat-card__number"><AnimatedNumber target={15} /> min</div>
        <div className="stat-card__label">wasted per manual handover summary</div>
      </div>
      <div className="stat-card">
        <div className="stat-card__number">1 in 5</div>
        <div className="stat-card__label">critical details missed in verbal handover</div>
      </div>
    </div>
  )
}
