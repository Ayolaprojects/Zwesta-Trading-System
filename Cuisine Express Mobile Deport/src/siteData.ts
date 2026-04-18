export type ContactKind = 'phone' | 'email' | 'address' | 'website'

export const contactItems: Array<{ label: string; value: string; kind: ContactKind }> = [
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

export const proofPoints = [
  { value: 'SA + SADC', label: 'regional supply coverage across South Africa and neighboring markets' },
  { value: '10ppm / 50ppm', label: 'diesel options structured for industrial and transport demand' },
  { value: 'Bulk + Contract', label: 'flexible transaction models for long-term and high-volume supply' },
]

export const missionPoints = [
  'Deliver high-quality fuel products',
  'Build long-term client partnerships',
  'Ensure efficient and secure supply chains',
  'Contribute to economic growth and energy security',
]

export const servicePillars = [
  {
    title: 'Fuel Supply & Trading',
    description:
      'Supply of diesel 10ppm and 50ppm, petrol ULP, paraffin, and jet fuel on request with structures tailored for bulk and contract clients.',
  },
  {
    title: 'Logistics & Distribution',
    description:
      'Road tanker deliveries, bulk transport coordination, depot access, and timed dispatch designed for safe regional movement of petroleum products.',
  },
  {
    title: 'Energy Solutions',
    description:
      'Fuel procurement strategy, supply-chain optimization, and project-based energy support for clients that need more than a basic reseller relationship.',
  },
]

export const industries = [
  {
    title: 'Mining',
    detail:
      'Fuel continuity for extraction, heavy equipment, generators, and remote operational support.',
  },
  {
    title: 'Transport & Logistics',
    detail:
      'Reliable diesel and petrol supply for fleets, depots, and route-dependent transport networks.',
  },
  {
    title: 'Agriculture',
    detail:
      'Support for seasonal demand, equipment fueling, and site-level storage planning.',
  },
  {
    title: 'Construction',
    detail:
      'Operational energy for contractors, mobile plant, and project sites where delivery timing affects productivity.',
  },
  {
    title: 'Government & Municipalities',
    detail:
      'Structured procurement support for public service operations requiring accountability and delivery consistency.',
  },
  {
    title: 'Independent Fuel Retailers',
    detail:
      'Wholesale access and structured supply support for retailers seeking dependable product flow.',
  },
]

export const advantages = [
  {
    title: 'Strategic Partnerships',
    detail:
      'Trusted supplier, logistics, and finance relationships improve execution and reduce transaction risk.',
  },
  {
    title: 'Flexible Deal Structures',
    detail:
      'Tank-to-Tank, bulk supply agreements, and escrow-based transactions aligned to client operating models.',
  },
  {
    title: 'Reliable Supply Chain',
    detail:
      'Access to storage facilities and distribution networks supports continuity across regions and sectors.',
  },
  {
    title: 'Empowerment & Growth',
    detail:
      'A commitment to transformation and inclusive economic development within the energy sector.',
  },
]

export const focusAreas = [
  {
    title: 'Multi-million litre diesel supply agreements',
    copy: 'Current growth is anchored in larger-scale diesel transactions built around long-range supply reliability.',
    image: '/images/gallery-storage.svg',
    alt: 'Illustrated fuel storage and supply scene',
  },
  {
    title: 'Long-term fuel supply contracts',
    copy: 'The company is focused on stable, relationship-led contracts for commercial and industrial buyers.',
    image: '/images/gallery-logistics.svg',
    alt: 'Illustrated tanker logistics and transport scene',
  },
  {
    title: 'Compliant regional execution',
    copy: 'Operations are positioned around secure, cost-effective, and compliant movement of petroleum products across the region.',
    image: '/images/gallery-trading.svg',
    alt: 'Illustrated energy trading and coordination scene',
  },
]
