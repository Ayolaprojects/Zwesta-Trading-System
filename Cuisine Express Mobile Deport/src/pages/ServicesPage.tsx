import { advantages, servicePillars } from '../siteData'
import { applyTilt, resetTilt } from '../tilt'

export function ServicesPage() {
  return (
    <>
      <section className="page-hero reveal-up">
        <p className="eyebrow">Services</p>
        <h1>Fuel, logistics, and energy solutions structured for commercial and industrial demand.</h1>
        <p className="lead">
          Cuisine Express Mobile Depot structures supply and transaction models around reliability,
          compliance, and scalable client demand.
        </p>
      </section>

      <section className="cards-section">
        <div className="card-grid">
          {servicePillars.map((pillar, index) => (
            <article
              className={`info-card tilt-surface reveal-up delay-${index + 1}`}
              key={pillar.title}
              onMouseMove={applyTilt}
              onMouseLeave={resetTilt}
            >
              <h3>{pillar.title}</h3>
              <p>{pillar.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="cards-section" id="advantage">
        <div className="section-heading reveal-up">
          <p className="eyebrow">Our advantage</p>
          <h2>Commercial flexibility backed by partnerships, infrastructure access, and disciplined execution.</h2>
        </div>
        <div className="card-grid card-grid-advantage">
          {advantages.map((item, index) => (
            <article
              className={`info-card tilt-surface reveal-up delay-${(index % 3) + 1}`}
              key={item.title}
              onMouseMove={applyTilt}
              onMouseLeave={resetTilt}
            >
              <h3>{item.title}</h3>
              <p>{item.detail}</p>
            </article>
          ))}
        </div>
      </section>
    </>
  )
}
