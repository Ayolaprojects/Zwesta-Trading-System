import { Link } from 'react-router-dom'
import { focusAreas, missionPoints, proofPoints } from '../siteData'
import { applyTilt, resetTilt } from '../tilt'

export function HomePage() {
  return (
    <>
      <section className="hero-section" id="hero">
        <div className="hero-copy reveal-up">
          <p className="eyebrow">Fuel supply. Petroleum trading. Regional energy logistics.</p>
          <h1>Reliable petroleum product supply across South Africa and the broader SADC region.</h1>
          <p className="lead">
            CUISINE EXPRESS MOBILE DEPOT is a dynamic energy company specializing in the supply,
            distribution, and trading of petroleum products. The business is positioned to deliver
            reliable, cost-effective, and compliant fuel solutions for commercial, industrial, mining,
            logistics, and retail sectors.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" to="/contact">
              Contact us
            </Link>
            <Link className="button button-secondary" to="/services">
              Explore services
            </Link>
          </div>
        </div>

        <div className="hero-visual reveal-up delay-1">
          <div className="hero-card hero-card-main tilt-surface" onMouseMove={applyTilt} onMouseLeave={resetTilt}>
            <img
              src="/images/hero-energy-metallic.svg"
              alt="Illustrated metallic fuel logistics and energy infrastructure scene"
              width="700"
              height="780"
            />
          </div>
          <div className="hero-card hero-card-note">
            <span>Core promise</span>
            <strong>Reliable, compliant, and cost-effective fuel supply for high-demand operations.</strong>
          </div>
        </div>
      </section>

      <section className="proof-strip reveal-up delay-2" aria-label="Business highlights">
        {proofPoints.map((item) => (
          <article className="tilt-surface" key={item.label} onMouseMove={applyTilt} onMouseLeave={resetTilt}>
            <strong>{item.value}</strong>
            <p>{item.label}</p>
          </article>
        ))}
      </section>

      <section className="section-grid" id="about">
        <div className="section-heading reveal-up">
          <p className="eyebrow">About the company</p>
          <h2>Built to become a trusted energy supplier with secure supply-chain execution across Africa.</h2>
        </div>
        <div className="split-panel reveal-up delay-1">
          <article className="story-card tilt-surface" onMouseMove={applyTilt} onMouseLeave={resetTilt}>
            <p className="eyebrow small-eyebrow">Vision</p>
            <p>To become a leading and trusted energy supplier across Africa.</p>
          </article>
          <article className="story-card tilt-surface" onMouseMove={applyTilt} onMouseLeave={resetTilt}>
            <p className="eyebrow small-eyebrow">Mission</p>
            <ul className="feature-list">
              {missionPoints.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </article>
        </div>
      </section>

      <section className="gallery-section" id="growth">
        <div className="section-heading reveal-up">
          <p className="eyebrow">Projects & growth</p>
          <h2>Current expansion is focused on larger diesel allocations and long-term supply agreements.</h2>
        </div>
        <div className="gallery-grid">
          {focusAreas.map((moment, index) => (
            <article
              className={`gallery-card tilt-surface reveal-up delay-${index + 1}`}
              key={moment.title}
              onMouseMove={applyTilt}
              onMouseLeave={resetTilt}
            >
              <img src={moment.image} alt={moment.alt} width="640" height="480" />
              <div>
                <h3>{moment.title}</h3>
                <p>{moment.copy}</p>
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  )
}
