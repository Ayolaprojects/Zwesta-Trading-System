import { NavLink, Outlet } from 'react-router-dom'
import { ContactIcon } from './ContactIcon'
import { contactItems } from './siteData'

export function Layout() {
  return (
    <div className="site-shell">
      <header className="topbar">
        <NavLink className="brand" to="/" aria-label="Cuisine Express home">
          <img
            className="brand-logo"
            src="/images/cuisine-logo.svg"
            alt="Cuisine Express Mobile Depot logo"
            width="112"
            height="112"
          />
          <span>
            <strong>Cuisine Express</strong>
            <small>Mobile Depot | Energy & Fuel Supply</small>
          </span>
        </NavLink>
        <nav className="topnav" aria-label="Primary navigation">
          <NavLink to="/">Home</NavLink>
          <NavLink to="/services">Services</NavLink>
          <NavLink to="/industries">Industries</NavLink>
          <NavLink to="/contact">Contact</NavLink>
        </nav>
      </header>

      <main>
        <Outlet />
        <footer className="contact-ribbon reveal-up">
          <div className="contact-ribbon__inner">
            <div className="contact-ribbon__grid">
              {contactItems.map((item) => (
                <article key={item.label} className="contact-ribbon__item">
                  <span className="contact-ribbon__icon" aria-hidden="true">
                    <ContactIcon kind={item.kind} />
                  </span>
                  <div>
                    <p className="contact-ribbon__label">{item.label}</p>
                    <p className="contact-ribbon__value">{item.value}</p>
                  </div>
                </article>
              ))}
            </div>
            <div className="contact-ribbon__accent" aria-hidden="true"></div>
          </div>
        </footer>
      </main>
    </div>
  )
}
