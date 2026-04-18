import { industries } from '../siteData'
import { applyTilt, resetTilt } from '../tilt'

export function IndustriesPage() {
  return (
    <>
      <section className="page-hero reveal-up">
        <p className="eyebrow">Industries we serve</p>
        <h1>Solutions tailored for the sectors where fuel continuity directly affects operations.</h1>
        <p className="lead">
          The business supports mining, transport, agriculture, construction, government, and independent retailers with dependable product flow.
        </p>
      </section>

      <section className="menu-section">
        <div className="menu-layout">
          <div className="menu-list">
            {industries.map((item, index) => (
              <article
                className={`menu-item tilt-surface reveal-up delay-${index + 1}`}
                key={item.title}
                onMouseMove={applyTilt}
                onMouseLeave={resetTilt}
              >
                <h3>{item.title}</h3>
                <p>{item.detail}</p>
              </article>
            ))}
          </div>
          <aside className="menu-aside tilt-surface reveal-up delay-3" onMouseMove={applyTilt} onMouseLeave={resetTilt}>
            <img
              src="/images/gallery-logistics.svg"
              alt="Illustrated fuel tanker and distribution scene"
              width="520"
              height="620"
            />
          </aside>
        </div>
      </section>
    </>
  )
}
