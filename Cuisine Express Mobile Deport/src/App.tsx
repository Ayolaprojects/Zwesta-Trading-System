import { useEffect, useState, type MouseEvent as ReactMouseEvent } from 'react'
import './App.css'
import {
  Fuel,
  Truck,
  Zap,
  Users,
  Database,
  FileText,
  CreditCard,
  Bell,
  Bot,
  Pickaxe,
  TruckIcon,
  Wheat,
  HardHat,
  Landmark,
  Store,
  Handshake,
  SlidersHorizontal,
  Link2,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
  Shield,
  BarChart3,
  ArrowRight,
  MapPin,
  Clock3,
  Navigation,
} from 'lucide-react'
import heroDepot from './assets/terminals-hero.jpg'
import tankerFleet from './assets/trucks.jpg'
import miningImage from './assets/Mining.jpeg'
import agricultureImage from './assets/Agric.webp'
import governmentImage from './assets/Govt Buildings.webp'
import constructionFuel from './assets/Bulk-Fuel-Australia.jpg'
import offshoreRig from './assets/Center.jpg'
import industrialConstruction from './assets/1-3-1.webp'
import qualityBadge from './assets/Quality.png'

const navLinks = [
  { href: '#services', label: 'Services' },
  { href: '#platform', label: 'Platform' },
  { href: '#industries', label: 'Industries' },
  { href: '#pricing', label: 'Pricing' },
  { href: '#growth', label: 'Growth' },
  { href: '#contact', label: 'Contact' },
]

const contactItems = [
  {
    label: 'Phone',
    value: '+27 10 023 6580 / +27 72 768 0323',
    kind: 'phone',
  },
  {
    label: 'Email',
    value: 'Punchjan@outlook.com',
    kind: 'email',
  },
  {
    label: 'Address',
    value: 'Florence Ribeiro Ave | Muckleneuk, Pretoria | 2021',
    kind: 'address',
  },
  {
    label: 'Website',
    value: 'www.cuisine.com',
    kind: 'website',
  },
]

const officeHours = [
  { label: 'Monday - Friday', value: '08:00 - 17:00' },
  { label: 'Saturday', value: 'By arrangement' },
  { label: 'Sunday', value: 'Closed' },
]

const proofPoints = [
  { value: 'SA + SADC', label: 'regional supply coverage across South Africa and neighboring markets' },
  { value: '10ppm / 50ppm', label: 'diesel options structured for industrial and transport demand' },
  { value: 'Bulk + Contract', label: 'flexible transaction models for long-term and high-volume supply' },
]

const infographicStages = [
  {
    title: 'Structured Product Supply',
    detail: 'Diesel 10ppm and 50ppm, petrol ULP, paraffin, and jet fuel on request for bulk and contract clients.',
    caption: 'Product layer',
    icon: Fuel,
  },
  {
    title: 'Regional Logistics Movement',
    detail: 'Road tanker dispatch, depot access, and timed routing keep supply synchronized with high-demand operations.',
    caption: 'Distribution layer',
    icon: Truck,
  },
  {
    title: 'Compliant Delivery Execution',
    detail: 'Commercial, industrial, mining, and public-sector customers receive disciplined, continuity-focused support.',
    caption: 'Execution layer',
    icon: Shield,
  },
]

const infographicFacts = [
  { label: 'Coverage', value: 'SA + SADC' },
  { label: 'Supply model', value: 'Bulk + Contract' },
  { label: 'Primary grades', value: '10ppm / 50ppm' },
]

const servicePillars = [
  {
    title: 'Fuel Supply & Trading',
    description:
      'Supply of diesel 10ppm and 50ppm, petrol ULP, paraffin, and jet fuel on request with structures tailored for bulk and contract clients.',
    icon: Fuel,
  },
  {
    title: 'Logistics & Distribution',
    description:
      'Road tanker deliveries, bulk transport coordination, depot access, and timed dispatch designed for safe regional movement of petroleum products.',
    icon: Truck,
  },
  {
    title: 'Energy Solutions',
    description:
      'Fuel procurement strategy, supply-chain optimization, and project-based energy support for clients that need more than a basic reseller relationship.',
    icon: Zap,
  },
]

const industries = [
  {
    title: 'Mining',
    detail:
      'Fuel continuity for extraction, heavy equipment, generators, and remote operational support.',
    icon: Pickaxe,
  },
  {
    title: 'Transport & Logistics',
    detail:
      'Reliable diesel and petrol supply for fleets, depots, and route-dependent transport networks.',
    icon: TruckIcon,
  },
  {
    title: 'Agriculture',
    detail:
      'Support for seasonal demand, equipment fueling, and site-level storage planning.',
    icon: Wheat,
  },
  {
    title: 'Construction',
    detail:
      'Operational energy for contractors, mobile plant, and project sites where delivery timing affects productivity.',
    icon: HardHat,
  },
  {
    title: 'Government & Municipalities',
    detail:
      'Structured procurement support for public service operations requiring accountability and delivery consistency.',
    icon: Landmark,
  },
  {
    title: 'Independent Fuel Retailers',
    detail:
      'Wholesale access and structured supply support for retailers seeking dependable product flow.',
    icon: Store,
  },
]

const advantages = [
  {
    title: 'Strategic Partnerships',
    detail:
      'Trusted supplier, logistics, and finance relationships improve execution and reduce transaction risk.',
    icon: Handshake,
  },
  {
    title: 'Flexible Deal Structures',
    detail:
      'Tank-to-Tank, bulk supply agreements, and escrow-based transactions aligned to client operating models.',
    icon: SlidersHorizontal,
  },
  {
    title: 'Reliable Supply Chain',
    detail:
      'Access to storage facilities and distribution networks supports continuity across regions and sectors.',
    icon: Link2,
  },
  {
    title: 'Empowerment & Growth',
    detail:
      'A commitment to transformation and inclusive economic development within the energy sector.',
    icon: TrendingUp,
  },
]

const focusAreas = [
  {
    title: 'Multi-million litre diesel supply agreements',
    copy: 'Current growth is anchored in larger-scale diesel transactions built around long-range supply reliability.',
    image: constructionFuel,
    alt: 'Bulk fuel supply support at an industrial site',
  },
  {
    title: 'Long-term fuel supply contracts',
    copy: 'The company is focused on stable, relationship-led contracts for commercial and industrial buyers.',
    image: tankerFleet,
    alt: 'Fuel tanker fleet and storage tanks',
  },
  {
    title: 'Compliant regional execution',
    copy: 'Operations are positioned around secure, cost-effective, and compliant movement of petroleum products across the region.',
    image: offshoreRig,
    alt: 'Offshore energy platform and operations',
  },
]

const platformScope = [
  {
    title: 'Customer accounts and regional CRM',
    description:
      'Secure onboarding, company profiles, document capture, and role-based account handling for South African buyers and regional commercial customers.',
    icon: Users,
  },
  {
    title: 'Catalog, pricing and quote engine',
    description:
      'Fuel product structures, region-aware pricing, quote requests, and approval-ready commercial flows for bulk and contract supply enquiries.',
    icon: Database,
  },
  {
    title: 'Orders, contracts and invoicing',
    description:
      'Quote-to-order conversion, recurring contract handling, invoice generation, and structured document records for repeat commercial transactions.',
    icon: FileText,
  },
  {
    title: 'Payments and transaction control',
    description:
      'Online payments, EFT reference capture, reconciliation-ready transaction logs, refund governance, and audit visibility across the platform.',
    icon: CreditCard,
  },
  {
    title: 'Admin workflows, alerts and reporting',
    description:
      'Back-office tools for sales, finance, and operations teams with notifications, approvals, tracking, and reporting across SA and neighbouring markets.',
    icon: Bell,
  },
  {
    title: 'AI sales and support agents',
    description:
      'AI agents for lead qualification, quote assistance, customer support, order-status guidance, and escalation into human teams with full conversation logging.',
    icon: Bot,
  },
]

const projectPhases = [
  {
    phase: 'Phase 1',
    title: 'Discovery, architecture and regional workflow design',
    amount: 'R35,000',
    description:
      'Business analysis, technical planning, database design, and workflow mapping for South African and regional operations.',
  },
  {
    phase: 'Phase 2',
    title: 'Core backend, identities and commercial data model',
    amount: 'R85,000',
    description:
      'Authentication, customer accounts, CRM records, product structures, pricing logic, and quote-request management.',
  },
  {
    phase: 'Phase 3',
    title: 'Orders, invoices, transactions and admin operations',
    amount: 'R110,000',
    description:
      'Order handling, contract workflows, invoice records, transaction capture, notifications, and admin control layers.',
  },
  {
    phase: 'Phase 4',
    title: 'AI agents, reporting and automation workflows',
    amount: 'R95,000',
    description:
      'AI sales and support agents, knowledge workflows, escalation controls, reporting, and internal operational summaries.',
  },
  {
    phase: 'Phase 5',
    title: 'Testing, deployment readiness and handover',
    amount: 'R45,000',
    description:
      'Quality assurance, deployment preparation, documentation, launch support, and structured project handover.',
  },
]

const carouselSlides = [
  {
    title: 'Storage Infrastructure',
    description: 'Depot and tank infrastructure supporting petroleum product storage and dispatch.',
    image: heroDepot,
    alt: 'Fuel terminal and storage depot',
  },
  {
    title: 'Logistics Fleet',
    description: 'Road tanker capacity for dependable fuel movement across key routes and clients.',
    image: tankerFleet,
    alt: 'Fuel tanker fleet lined up at storage tanks',
  },
  {
    title: 'Mining Supply Support',
    description: 'Heavy-industry fuel support for large-scale mining and extraction environments.',
    image: miningImage,
    alt: 'Mining trucks operating in an open pit mine',
  },
  {
    title: 'Agriculture Energy Support',
    description: 'Fuel continuity for agricultural machinery, transport, and seasonal operations.',
    image: agricultureImage,
    alt: 'Agricultural machinery at sunset',
  },
  {
    title: 'Government & Public Sector',
    description: 'Structured supply support for public service and municipal operations.',
    image: governmentImage,
    alt: 'Government buildings representing public sector supply',
  },
  {
    title: 'Construction Fuel Support',
    description: 'Fuel support for heavy equipment, infrastructure work, and industrial site execution.',
    image: industrialConstruction,
    alt: 'Construction equipment and fuel tanker at an industrial site',
  },
]

function applyTilt(event: ReactMouseEvent<HTMLElement>) {
  const rect = event.currentTarget.getBoundingClientRect()
  const x = (event.clientX - rect.left) / rect.width
  const y = (event.clientY - rect.top) / rect.height
  const rotateY = (x - 0.5) * 14
  const rotateX = (0.5 - y) * 12

  event.currentTarget.style.setProperty('--tilt-x', `${rotateX.toFixed(2)}deg`)
  event.currentTarget.style.setProperty('--tilt-y', `${rotateY.toFixed(2)}deg`)
  event.currentTarget.style.setProperty('--glow-x', `${(x * 100).toFixed(2)}%`)
  event.currentTarget.style.setProperty('--glow-y', `${(y * 100).toFixed(2)}%`)
}

function resetTilt(event: ReactMouseEvent<HTMLElement>) {
  event.currentTarget.style.setProperty('--tilt-x', '0deg')
  event.currentTarget.style.setProperty('--tilt-y', '0deg')
  event.currentTarget.style.setProperty('--glow-x', '50%')
  event.currentTarget.style.setProperty('--glow-y', '50%')
}

function ContactIcon({ kind }: { kind: string }) {
  if (kind === 'phone') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M6.6 10.8C8.4 14.3 9.7 15.6 13.2 17.4L15.9 14.7C16.2 14.4 16.6 14.3 17 14.4C18.3 14.8 19.7 15 21 15C21.6 15 22 15.4 22 16V20C22 20.6 21.6 21 21 21C10.5 21 3 13.5 3 3C3 2.4 3.4 2 4 2H8C8.6 2 9 2.4 9 3C9 4.3 9.2 5.7 9.6 7C9.7 7.4 9.6 7.8 9.3 8.1L6.6 10.8Z" fill="currentColor"/>
      </svg>
    )
  }

  if (kind === 'email') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M4 5H20C21.1 5 22 5.9 22 7V17C22 18.1 21.1 19 20 19H4C2.9 19 2 18.1 2 17V7C2 5.9 2.9 5 4 5ZM4 8.2V17H20V8.2L12 13.4L4 8.2ZM12 11.1L19.6 7H4.4L12 11.1Z" fill="currentColor"/>
      </svg>
    )
  }

  if (kind === 'address') {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 2C8.1 2 5 5.1 5 9C5 14.2 12 22 12 22C12 22 19 14.2 19 9C19 5.1 15.9 2 12 2ZM12 11.5C10.6 11.5 9.5 10.4 9.5 9C9.5 7.6 10.6 6.5 12 6.5C13.4 6.5 14.5 7.6 14.5 9C14.5 10.4 13.4 11.5 12 11.5Z" fill="currentColor"/>
      </svg>
    )
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 2C6.5 2 2 6.5 2 12C2 17.5 6.5 22 12 22C17.5 22 22 17.5 22 12C22 6.5 17.5 2 12 2ZM18.9 8H15.7C15.3 6.4 14.7 4.9 13.9 3.8C16 4.4 17.7 5.9 18.9 8ZM12 4.1C12.9 5.3 13.7 6.6 14.1 8H9.9C10.3 6.6 11.1 5.3 12 4.1ZM4.3 14C4.1 13.4 4 12.7 4 12C4 11.3 4.1 10.6 4.3 10H8.6C8.5 10.7 8.5 11.3 8.5 12C8.5 12.7 8.5 13.3 8.6 14H4.3ZM5.1 16H8.9C9.3 17.6 9.9 19.1 10.7 20.2C8.5 19.6 6.8 18.1 5.1 16ZM8.9 8H5.1C6.3 5.9 8 4.4 10.1 3.8C9.3 4.9 8.7 6.4 8.9 8ZM12 19.9C11.1 18.7 10.3 17.4 9.9 16H14.1C13.7 17.4 12.9 18.7 12 19.9ZM14.4 14H9.6C9.5 13.3 9.5 12.7 9.5 12C9.5 11.3 9.5 10.7 9.6 10H14.4C14.5 10.7 14.5 11.3 14.5 12C14.5 12.7 14.5 13.3 14.4 14ZM13.9 20.2C14.7 19.1 15.3 17.6 15.7 16H18.9C17.7 18.1 16 19.6 13.9 20.2ZM16.3 14C16.4 13.3 16.5 12.7 16.5 12C16.5 11.3 16.4 10.7 16.3 10H19.7C19.9 10.6 20 11.3 20 12C20 12.7 19.9 13.4 19.7 14H16.3Z" fill="currentColor"/>
    </svg>
  )
}

function App() {
  const [carouselIndex, setCarouselIndex] = useState(0)
  const [isCarouselPaused, setIsCarouselPaused] = useState(false)
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  useEffect(() => {
    if (isCarouselPaused) {
      return undefined
    }

    const intervalId = window.setInterval(() => {
      setCarouselIndex((currentIndex) => (currentIndex + 1) % carouselSlides.length)
    }, 4000)

    return () => window.clearInterval(intervalId)
  }, [isCarouselPaused])

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 760) {
        setIsMenuOpen(false)
      }
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsMenuOpen(false)
      }
    }

    window.addEventListener('resize', handleResize)
    window.addEventListener('keydown', handleKeyDown)

    return () => {
      window.removeEventListener('resize', handleResize)
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [])

  const previousSlide = () => {
    setCarouselIndex((currentIndex) =>
      currentIndex === 0 ? carouselSlides.length - 1 : currentIndex - 1,
    )
  }

  const nextSlide = () => {
    setCarouselIndex((currentIndex) => (currentIndex + 1) % carouselSlides.length)
  }

  return (
    <div className="site-shell">
      <header className={`topbar${isMenuOpen ? ' is-menu-open' : ''}`}>
        <a className="brand" href="#hero" aria-label="Cuisine Express home">
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
        </a>
        <button
          type="button"
          className={`menu-toggle${isMenuOpen ? ' is-open' : ''}`}
          aria-expanded={isMenuOpen}
          aria-controls="primary-navigation"
          aria-label={isMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
          onClick={() => setIsMenuOpen((currentState) => !currentState)}
        >
          <span></span>
          <span></span>
          <span></span>
        </button>
        <nav
          className={`topnav${isMenuOpen ? ' is-open' : ''}`}
          id="primary-navigation"
          aria-label="Primary navigation"
        >
          {navLinks.map((link) => (
            <a key={link.href} href={link.href} onClick={() => setIsMenuOpen(false)}>
              {link.label}
            </a>
          ))}
        </nav>
      </header>

      <main>
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
              <a className="button button-primary" href="#contact">
                Contact us <ArrowRight size={18} aria-hidden="true" />
              </a>
              <a className="button button-secondary" href="#services">
                Explore services <ArrowRight size={18} aria-hidden="true" />
              </a>
              <a
                className="button button-tertiary"
                href="https://www.google.com/maps/search/?api=1&query=Florence+Ribeiro+Ave,+Muckleneuk,+Pretoria+2021"
                target="_blank"
                rel="noreferrer"
              >
                Get directions <Navigation size={18} aria-hidden="true" />
              </a>
            </div>
          </div>

          <div className="hero-visual reveal-up delay-1">
            <img
              className="premium-badge"
              src={qualityBadge}
              alt="Premium quality guaranteed badge"
              width="220"
              height="220"
            />
            <div
              className="hero-card hero-card-main tilt-surface"
              onMouseMove={applyTilt}
              onMouseLeave={resetTilt}
            >
              <img
                src={heroDepot}
                alt="Fuel terminal and storage depot"
                width="700"
                height="780"
              />
            </div>
            <div className="hero-card hero-card-note gold-edge-glow">
              <span>Core promise</span>
              <strong>Reliable, compliant, and cost-effective fuel supply for high-demand operations.</strong>
            </div>
          </div>
        </section>

        <section className="proof-strip reveal-up delay-2" aria-label="Business highlights">
          {proofPoints.map((item) => (
            <article
              className="tilt-surface"
              key={item.label}
              onMouseMove={applyTilt}
              onMouseLeave={resetTilt}
            >
              <span className="proof-badge" aria-hidden="true">
                <BarChart3 size={22} className="proof-icon" />
              </span>
              <strong>{item.value}</strong>
              <p>{item.label}</p>
            </article>
          ))}
        </section>

        <section className="infographic-section" id="snapshot">
          <div className="section-heading reveal-up">
            <p className="eyebrow">Operational snapshot</p>
            <h2>An infographic view of how supply, movement, and delivery fit together.</h2>
            <ul className="section-heading__points">
              <li>Structured product sourcing built around grade reliability and client-specific volume needs.</li>
              <li>Route-optimised logistics planning that keeps regional movements efficient and predictable.</li>
              <li>Compliant last-mile delivery designed for continuity at mines, fleets, depots, and industrial sites.</li>
            </ul>
          </div>
          <div className="infographic-layout reveal-up delay-1">
            <div
              className="infographic-flow tilt-surface"
              onMouseMove={applyTilt}
              onMouseLeave={resetTilt}
            >
              {infographicStages.map((stage, index) => (
                <article className="infographic-step" key={stage.title}>
                  <span className="infographic-step__rail" aria-hidden="true">
                    <span className="infographic-step__index">0{index + 1}</span>
                  </span>
                  <span className="infographic-step__icon" aria-hidden="true">
                    <stage.icon size={24} />
                  </span>
                  <div className="infographic-step__body">
                    <p className="infographic-step__caption">{stage.caption}</p>
                    <h3>{stage.title}</h3>
                    <p>{stage.detail}</p>
                  </div>
                </article>
              ))}
            </div>

            <aside
              className="infographic-panel tilt-surface gold-edge-glow"
              onMouseMove={applyTilt}
              onMouseLeave={resetTilt}
            >
              <div className="infographic-panel__intro">
                <span className="infographic-panel__icon" aria-hidden="true">
                  <BarChart3 size={24} />
                </span>
                <div>
                  <p className="eyebrow small-eyebrow">At a glance</p>
                  <h3>Commercial structure built for bulk petroleum execution.</h3>
                </div>
              </div>

              <div className="infographic-facts" aria-label="Operating facts">
                {infographicFacts.map((fact) => (
                  <article key={fact.label} className="infographic-fact">
                    <p className="infographic-fact__label">{fact.label}</p>
                    <strong>{fact.value}</strong>
                  </article>
                ))}
              </div>

              <div className="infographic-panel__note">
                <p>
                  The model combines product access, logistics coordination, and disciplined delivery to support dependable fuel continuity across South Africa and the broader SADC region.
                </p>
              </div>
            </aside>
          </div>
        </section>

        <section className="carousel-section reveal-up" id="operations">
          <div className="section-heading">
            <p className="eyebrow">Operations gallery</p>
            <h2>Real site imagery for storage, transport, mining, agriculture, retail, and public-sector positioning.</h2>
            <ul className="section-heading__points">
              <li>Terminal and depot infrastructure that supports petroleum storage, staging, and dispatch readiness.</li>
              <li>Fleet dispatch operations that reflect real transport execution across high-demand delivery routes.</li>
              <li>On-site industrial delivery environments showing how supply supports active field operations.</li>
            </ul>
          </div>
          <div
            className="carousel-shell tilt-surface"
            onMouseMove={applyTilt}
            onMouseLeave={(event) => {
              resetTilt(event)
              setIsCarouselPaused(false)
            }}
            onMouseEnter={() => setIsCarouselPaused(true)}
          >
            <div className="carousel-stage">
              <img
                src={carouselSlides[carouselIndex].image}
                alt={carouselSlides[carouselIndex].alt}
                className="carousel-image"
                width="1280"
                height="760"
              />
              <div className="carousel-overlay">
                <p className="eyebrow">Featured asset</p>
                <h3>{carouselSlides[carouselIndex].title}</h3>
                <p>{carouselSlides[carouselIndex].description}</p>
              </div>
              <button className="carousel-nav carousel-nav-prev" type="button" onClick={previousSlide} aria-label="Previous slide">
                <ChevronLeft size={18} aria-hidden="true" /> Prev
              </button>
              <button className="carousel-nav carousel-nav-next" type="button" onClick={nextSlide} aria-label="Next slide">
                Next <ChevronRight size={18} aria-hidden="true" />
              </button>
            </div>
            <div className="carousel-track" aria-label="Carousel slide selector">
              {carouselSlides.map((slide, index) => (
                <button
                  key={slide.title}
                  type="button"
                  className={`carousel-thumb${index === carouselIndex ? ' is-active' : ''}`}
                  onClick={() => setCarouselIndex(index)}
                >
                  <img src={slide.image} alt="" width="220" height="120" />
                  <span>{slide.title}</span>
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="cards-section" id="services">
          <div className="section-heading reveal-up">
            <p className="eyebrow">Services</p>
            <h2>Fuel, logistics, and energy solutions structured for commercial and industrial demand.</h2>
            <ul className="section-heading__points">
              <li>Diesel 10ppm and 50ppm supply structured for recurring commercial and industrial consumption.</li>
              <li>Road tanker logistics coordinated for safe movement, timed delivery, and supply continuity.</li>
              <li>Energy procurement support that helps clients plan supply strategy beyond one-off transactions.</li>
            </ul>
          </div>
          <div className="card-grid">
            {servicePillars.map((pillar, index) => (
              <article
                className={`info-card tilt-surface reveal-up delay-${index + 1}`}
                key={pillar.title}
                onMouseMove={applyTilt}
                onMouseLeave={resetTilt}
              >
                <span className="card-icon card-icon--service" aria-hidden="true"><pillar.icon size={30} /></span>
                <h3>{pillar.title}</h3>
                <p>{pillar.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="menu-section" id="industries">
          <div className="section-heading reveal-up">
            <p className="eyebrow">Industries we serve</p>
            <h2>Solutions tailored for the sectors where fuel continuity directly affects operations.</h2>
            <ul className="section-heading__points">
              <li>Mining and extraction operations that depend on dependable supply for equipment and remote sites.</li>
              <li>Transport and fleet businesses that need disciplined fuel flow to protect route performance.</li>
              <li>Agriculture and construction clients with seasonal demand, site activity, and mobile asset needs.</li>
              <li>Government and retail customers requiring accountability, consistency, and structured procurement support.</li>
            </ul>
          </div>
          <div className="menu-layout">
            <div className="menu-list">
              {industries.map((item, index) => (
                <article
                  className={`menu-item tilt-surface reveal-up delay-${index + 1}`}
                  key={item.title}
                  onMouseMove={applyTilt}
                  onMouseLeave={resetTilt}
                >
                  <span className="card-icon card-icon--industry" aria-hidden="true"><item.icon size={28} /></span>
                  <h3>{item.title}</h3>
                  <p>{item.detail}</p>
                </article>
              ))}
            </div>
            <aside
              className="menu-aside tilt-surface reveal-up delay-3"
              onMouseMove={applyTilt}
              onMouseLeave={resetTilt}
            >
              <img
                src={tankerFleet}
                alt="Fuel tanker fleet and storage scene"
                width="520"
                height="620"
              />
            </aside>
          </div>
        </section>

        <section className="cards-section" id="advantage">
          <div className="section-heading reveal-up">
            <p className="eyebrow">Our advantage</p>
            <h2>Commercial flexibility backed by partnerships, infrastructure access, and disciplined execution.</h2>
            <ul className="section-heading__points">
              <li>Trusted supplier partnerships that strengthen reliability, pricing confidence, and transaction execution.</li>
              <li>Flexible deal structures shaped around bulk allocations, contract terms, and client operating models.</li>
              <li>Depot and network access that improves reach, responsiveness, and supply-chain resilience.</li>
            </ul>
          </div>
          <div className="card-grid card-grid-advantage">
            {advantages.map((item, index) => (
              <article
                className={`info-card tilt-surface reveal-up delay-${(index % 3) + 1}`}
                key={item.title}
                onMouseMove={applyTilt}
                onMouseLeave={resetTilt}
              >
                <span className="card-icon card-icon--advantage" aria-hidden="true"><item.icon size={30} /></span>
                <h3>{item.title}</h3>
                <p>{item.detail}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="cards-section" id="platform">
          <div className="section-heading reveal-up">
            <p className="eyebrow">Platform scope</p>
            <h2>Full backend scope for online sales, transactions, and AI-assisted customer operations across South Africa and regional markets.</h2>
            <ul className="section-heading__points">
              <li>Built for South African supply operations and regional commercial expansion.</li>
              <li>Structured around customers, payments, contracts, and operational reporting.</li>
              <li>Designed as a production platform rather than a basic brochure backend.</li>
            </ul>
          </div>
          <div className="card-grid">
            {platformScope.map((item, index) => (
              <article
                className={`info-card pricing-card tilt-surface reveal-up delay-${(index % 3) + 1}`}
                key={item.title}
                onMouseMove={applyTilt}
                onMouseLeave={resetTilt}
              >
                <span className="card-icon card-icon--service" aria-hidden="true"><item.icon size={30} /></span>
                <p className="pricing-card__phase">Scope module</p>
                <h3>{item.title}</h3>
                <p>{item.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="gallery-section" id="growth">
          <div className="section-heading reveal-up">
            <p className="eyebrow">Projects & growth</p>
            <h2>Current expansion is focused on larger diesel allocations and long-term supply agreements.</h2>
            <ul className="section-heading__points">
              <li>Multi-million litre contract opportunities that reflect larger-scale demand and supply confidence.</li>
              <li>Long-term supply partnerships focused on stability, planning visibility, and repeat execution.</li>
              <li>Regional compliance expansion aligned with secure, cost-effective petroleum movement across markets.</li>
            </ul>
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

        <section className="gallery-section" id="pricing">
          <div className="section-heading reveal-up">
            <p className="eyebrow">Project pricing</p>
            <h2>Phase-based commercial pricing for a production-ready backend rollout serving South Africa and neighbouring regions.</h2>
            <ul className="section-heading__points">
              <li>Quoted as a full operational platform covering online sales, transactions, and AI support.</li>
              <li>Excludes VAT, hosting, payment gateway charges, and third-party AI usage costs.</li>
              <li>Designed to support SA first, with regional expansion into SADC and other approved markets.</li>
            </ul>
          </div>
          <div className="pricing-grid">
            {projectPhases.map((phase, index) => (
              <article
                className={`info-card pricing-card tilt-surface reveal-up delay-${(index % 3) + 1}`}
                key={phase.title}
                onMouseMove={applyTilt}
                onMouseLeave={resetTilt}
              >
                <p className="pricing-card__phase">{phase.phase}</p>
                <strong className="pricing-card__amount">{phase.amount}</strong>
                <h3>{phase.title}</h3>
                <p>{phase.description}</p>
              </article>
            ))}
          </div>
          <aside className="pricing-summary gold-edge-glow reveal-up delay-2">
            <p className="eyebrow">Commercial summary</p>
            <h3>Recommended full-scope quotation</h3>
            <strong className="pricing-summary__total">R370,000</strong>
            <p className="pricing-summary__note">
              Estimated total for the backend platform only, excluding VAT and third-party operating costs.
            </p>
            <ul className="pricing-summary__list">
              <li>Supports customers, quotations, transactions, invoices, and admin workflows.</li>
              <li>Includes AI agent capability for sales support, support operations, and escalation logic.</li>
              <li>Structured for South Africa first, with regional commercial readiness built into the rollout.</li>
            </ul>
          </aside>
        </section>

        <section className="cta-section reveal-up" id="contact">
          <div className="contact-layout">
            <div className="contact-intro">
              <p className="eyebrow">Contact page</p>
              <h2>We are ready to support your fuel and gas requirements.</h2>
              <p className="contact-intro__copy">
                Speak with Cuisine Express Mobile Depot for petroleum product supply, logistics coordination,
                and long-term fuel contract support across South Africa and the SADC region.
              </p>
            </div>

            <article className="map-card tilt-surface gold-edge-glow" onMouseMove={applyTilt} onMouseLeave={resetTilt}>
              <div className="map-card__header">
                <span className="map-card__icon" aria-hidden="true">
                  <MapPin size={22} />
                </span>
                <div>
                  <p className="eyebrow small-eyebrow">Office location</p>
                  <h3>Florence Ribeiro Ave, Muckleneuk, Pretoria</h3>
                </div>
              </div>

              <div className="map-frame-wrap">
                <iframe
                  className="map-frame"
                  title="Cuisine Express Mobile Depot location map"
                  src="https://www.google.com/maps?q=Florence%20Ribeiro%20Ave%2C%20Muckleneuk%2C%20Pretoria%202021&z=15&output=embed"
                  loading="lazy"
                  referrerPolicy="no-referrer-when-downgrade"
                />
              </div>

              <div className="map-meta">
                <article className="map-meta__card">
                  <div className="map-meta__header">
                    <span className="map-meta__icon" aria-hidden="true">
                      <Clock3 size={18} />
                    </span>
                    <div>
                      <p className="eyebrow small-eyebrow">Office hours</p>
                      <h4>Availability</h4>
                    </div>
                  </div>
                  <div className="hours-list">
                    {officeHours.map((item) => (
                      <div className="hours-list__row" key={item.label}>
                        <span>{item.label}</span>
                        <strong>{item.value}</strong>
                      </div>
                    ))}
                  </div>
                </article>

                <article className="map-meta__card map-meta__card--accent">
                  <p className="eyebrow small-eyebrow">Response window</p>
                  <h4>Best for visits and meetings</h4>
                  <p>
                    Pre-arranged visits during weekday business hours are the best fit for contract discussions,
                    logistics coordination, and supply planning.
                  </p>
                </article>
              </div>

              <div className="map-card__footer">
                <p>Visit us in Pretoria for supply discussions, logistics planning, and contract coordination.</p>
                <a
                  className="map-link"
                  href="https://www.google.com/maps/search/?api=1&query=Florence+Ribeiro+Ave,+Muckleneuk,+Pretoria+2021"
                  target="_blank"
                  rel="noreferrer"
                >
                  Open in Maps <ArrowRight size={18} aria-hidden="true" />
                </a>
              </div>
            </article>
          </div>
        </section>

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

export default App
