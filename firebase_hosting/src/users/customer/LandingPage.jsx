import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Sparkles, ShoppingBag, ShieldCheck, Truck, LifeBuoy, CheckCircle, Lock, ChevronLeft, ChevronRight, ArrowRight, Search, X
} from 'lucide-react';

import QueryForm from './QueryForm';
import {
  Repeat, TrendingUp, MessageSquare, Tag, Building2, Gavel, Recycle, Boxes, ArrowLeftRight, Timer, Mic, Leaf, Camera,
  ShoppingCart, Wallet, QrCode, Bell, ScanLine, Wrench, Puzzle, Award, BarChart3, Scale, Star, Lightbulb, Languages, Gauge
} from 'lucide-react';
import { CORE_CAPABILITIES, BIDDING, REVERSE_LOGISTICS, LIFECYCLE_FEATURES } from './features';

const SERVICES = [
  {
    code: 'MaaS',
    title: 'Management as a Service',
    summary: 'Role access, user listing and databases.',
    icon: ShieldCheck,
    accent: 'border-t-google-red',
    iconBox: 'bg-google-red-light text-google-red',
    features: [
      'Role-based access control for Owner, Consumer and Customer',
      'Multi-tenant workspaces with team and role management for owners and sellers',
      'Usage and quota tracking for every workspace',
      'Live system health monitoring across every service',
      'Budget tracking with alerts and a kill switch at the cap',
      'Analytics dashboards on sales and spend data'
    ]
  },
  {
    code: 'PaaS',
    title: 'Product as a Service',
    summary: 'List, sell and buy products.',
    icon: ShoppingBag,
    accent: 'border-t-google-blue',
    iconBox: 'bg-google-blue-light text-google-blue',
    features: [
      'Product catalog with condition grades and carbon footprint',
      'Customer-to-Multi-Seller live bidding',
      'Surplus auctions for excess stock',
      'AI demand forecasting with reorder points',
      'Stock and pricing across new, refurbished and open-box items'
    ]
  },
  {
    code: 'TaaS',
    title: 'Transport as a Service',
    summary: 'Move goods from A to B.',
    icon: Truck,
    accent: 'border-t-google-green',
    iconBox: 'bg-google-green-light text-google-green',
    features: [
      'Shipment tracking with carrier and ETA',
      'Forward delivery and peer-to-peer reverse logistics',
      'Return routing by condition grade: resale, refurbish or recycle',
      'Refurbisher dispatch',
      'CO2 savings reported per shipment'
    ]
  },
  {
    code: 'SaaS',
    title: 'Support as a Service',
    summary: 'Queries, after-sales and repairs.',
    icon: LifeBuoy,
    accent: 'border-t-google-yellow',
    iconBox: 'bg-google-yellow-light text-[#B06000]',
    features: [
      'AI shopping and support assistant',
      'Photo-based return grading with recovery estimate and recommended channel',
      'Secure return photo upload',
      'Support ticket tracking with priority and status',
      'After-sales and warranty handling'
    ]
  }
];

const SECTION = 'w-full px-4 sm:px-8 lg:px-12 2xl:px-20';

// Fades and lifts its content in once it scrolls into view
function Reveal({ children, delay = 0, className = '' }) {
  const ref = useRef(null);
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === 'undefined') { setSeen(true); return undefined; }
    const io = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) { setSeen(true); io.disconnect(); } }, { threshold: 0.12 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return <div ref={ref} style={{ transitionDelay: `${delay}ms` }} className={`reveal ${seen ? 'in' : ''} ${className}`}>{children}</div>;
}

// A number that counts up the first time it is seen
function Counter({ to, suffix = '' }) {
  const ref = useRef(null);
  const [n, setN] = useState(0);
  useEffect(() => {
    const el = ref.current;
    const run = () => {
      const start = performance.now();
      const tick = (now) => { const t = Math.min(1, (now - start) / 1200); setN(Math.round(to * (1 - Math.pow(1 - t, 3)))); if (t < 1) requestAnimationFrame(tick); };
      requestAnimationFrame(tick);
    };
    if (!el || typeof IntersectionObserver === 'undefined') { setN(to); return undefined; }
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { run(); io.disconnect(); } }, { threshold: 0.4 });
    io.observe(el);
    return () => io.disconnect();
  }, [to]);
  return <span ref={ref}>{n}{suffix}</span>;
}

const scrollToId = (id) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });

// Illustrations live in public/images
const BANNER_IMAGE = 'w-full h-auto sm:w-auto sm:h-[400px] max-w-full justify-self-center xl:justify-self-end rounded-2xl shadow-2xl';
// Bump when the illustrations are redrawn (scripts/gen_illustrations.py), so browsers fetch the new pictures
const IMAGES_VERSION = '5';
const serviceImage = (svc) => `/images/${svc.code.toLowerCase()}.svg?v=${IMAGES_VERSION}`;

const SERVICE_PITCH = {
  MaaS: 'Run the platform and every seller workspace with confidence: who can do what, how it is performing and what it costs.',
  PaaS: 'Turn every product into a market: list it, sell it, let sellers bid for it and plan stock with AI forecasts.',
  TaaS: 'Move goods forward and back with full visibility, and route every return to its best next life.',
  SaaS: 'Answer questions, grade returns from a photo and keep every ticket moving with AI support.'
};

const SLIDE_COUNT = SERVICES.length + 1;
const SLIDE_INTERVAL_MS = 6000;

// Banner carousel: slide 1 shows every service in one picture, then one slide per service.
// Auto-advances, pauses on hover, and can be driven with the dots or the arrows.
function HeroCarousel({ onOpenSignIn }) {
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (paused || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined;
    const timer = setInterval(() => setActive((i) => (i + 1) % SLIDE_COUNT), SLIDE_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [paused]);

  const go = (index) => setActive((index + SLIDE_COUNT) % SLIDE_COUNT);
  const labels = ['Overview', ...SERVICES.map((svc) => svc.code)];

  return (
    <section
      className="google-hero gradient-pan text-white relative overflow-hidden flex flex-col"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <div className="animate-drift pointer-events-none absolute -top-24 -right-24 h-96 w-96 rounded-full bg-google-yellow/25 blur-2xl" />
      <div className="animate-drift pointer-events-none absolute -bottom-32 left-1/3 h-80 w-80 rounded-full bg-google-red/25 blur-2xl [animation-delay:-5s]" />
      <div className="animate-float pointer-events-none absolute top-10 left-8 h-40 w-40 rounded-full bg-google-green/25 blur-2xl" />

      <div className="relative z-10 flex-1 overflow-hidden flex">
        <div
          className="flex w-full transition-transform duration-700 ease-in-out"
          style={{ transform: `translateX(-${active * 100}%)` }}
        >
          {/* Slide 1: all services in one */}
          <div className="w-full shrink-0 flex" aria-hidden={active !== 0}>
            <div className={`${SECTION} py-8 sm:py-10 flex items-center w-full`}>
              <div className="grid grid-cols-1 xl:grid-cols-[5fr_7fr] gap-12 items-center w-full">
                <div className="space-y-6">
                  <h1 className="text-3xl sm:text-4xl 2xl:text-5xl font-extrabold tracking-tight leading-tight">
                    Intelligent <span className="google-underline">360° commerce</span>, from first sale to final reuse
                  </h1>
                  <p className="text-lg text-white/85 leading-relaxed max-w-2xl">
                    Unify sourcing, inventory forecasting, multi-seller bidding, delivery and AI-driven returns in one connected platform, so every product gets a second life.
                  </p>
                  <div className="flex flex-wrap gap-3 pt-1">
                    <button type="button" onClick={onOpenSignIn} className="group inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-base font-semibold text-google-teal-dark shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl">
                      Sign in to the platform <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                    </button>
                    <button type="button" onClick={() => scrollToId('services')} className="inline-flex items-center gap-2 rounded-xl border border-white/50 px-6 py-3 text-base font-semibold text-white transition hover:bg-white/15">
                      Explore services
                    </button>
                  </div>
                </div>
                {/* In 3D: the console leans back towards the centre, the service cards lean back towards it too */}
                <div className="flex h-[210px] sm:h-[400px] w-full max-w-full items-center justify-center gap-2 sm:gap-4 justify-self-center xl:justify-self-end [perspective:1400px]"
                  role="img" aria-label="The Lakshmi console with its four services, and what each one does">
                  <img src={`/images/overview-console.svg?v=${IMAGES_VERSION}`} alt="" aria-hidden="true"
                    className="h-[78%] w-auto min-w-0 max-w-[68%] [transform:rotateY(18deg)] [transform-origin:left_center]" />
                  <img src={`/images/overview-cards.svg?v=${IMAGES_VERSION}`} alt="" aria-hidden="true"
                    className="h-full w-auto min-w-0 max-w-[30%] [transform:rotateY(-18deg)] [transform-origin:right_center]" />
                </div>
              </div>
            </div>
          </div>

          {/* One slide per service */}
          {SERVICES.map((svc, i) => (
            <div key={svc.code} className="w-full shrink-0 flex" aria-hidden={active !== i + 1}>
              <div className={`${SECTION} py-8 sm:py-10 flex items-center w-full`}>
                <div className="grid grid-cols-1 xl:grid-cols-[5fr_7fr] gap-12 items-center w-full">
                  <div className="space-y-6">
                    <span className="inline-block px-3.5 py-1 bg-white/15 rounded-full text-xs font-bold uppercase tracking-wider">
                      {svc.code} · Service {i + 1} of {SERVICES.length}
                    </span>
                    <h2 className="text-3xl sm:text-4xl 2xl:text-5xl font-extrabold tracking-tight leading-tight">
                      <span className="google-underline">{svc.title}</span>
                    </h2>
                    <p className="text-lg text-white/85 leading-relaxed max-w-2xl">{SERVICE_PITCH[svc.code]}</p>
                  </div>

                  <img src={serviceImage(svc)} alt={`${svc.title} illustration`} className={BANNER_IMAGE} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Controls: arrows and dots */}
      <div className="relative z-10 pb-5 flex items-center justify-center gap-5">
        <button
          onClick={() => go(active - 1)}
          aria-label="Previous slide"
          className="p-2 rounded-full border border-white/30 hover:bg-white/10 transition-colors"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-3">
          {labels.map((label, index) => (
            <button
              key={label}
              onClick={() => go(index)}
              aria-label={`Show ${label}`}
              aria-current={active === index}
              className={`h-3 rounded-full transition-all duration-300 ${
                active === index ? 'w-10 bg-white' : 'w-3 bg-white/40 hover:bg-white/70'
              }`}
            />
          ))}
        </div>
        <button
          onClick={() => go(active + 1)}
          aria-label="Next slide"
          className="p-2 rounded-full border border-white/30 hover:bg-white/10 transition-colors"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
      </div>
    </section>
  );
}

function SectionHeading({ eyebrow, title, text, center }) {
  return (
    <div className={`mb-10 ${center ? 'text-center mx-auto max-w-3xl' : 'max-w-3xl'}`}>
      <span className="inline-block text-xs font-bold text-google-teal uppercase tracking-wider mb-2 pb-1 border-b-2 border-transparent" style={{ borderImage: "linear-gradient(90deg, #4285F4, #EA4335, #FBBC04, #34A853) 1" }}>{eyebrow}</span>
      <h2 className="text-3xl sm:text-4xl font-bold text-google-teal-dark tracking-tight">{title}</h2>
      {text && <p className="mt-3 text-base text-google-gray-600 leading-relaxed">{text}</p>}
    </div>
  );
}

// Every feature is a tile of the colour of the service it belongs to
const SERVICE_TILE = {
  MaaS: 'bg-google-red-light text-google-red',
  PaaS: 'bg-google-blue-light text-google-blue',
  TaaS: 'bg-google-green-light text-google-green',
  SaaS: 'bg-google-yellow-light text-[#B06000]'
};

// feature name -> its own icon and the service it belongs to
const FEATURE_META = {
  'End-to-end lifecycle management': { icon: Repeat, service: 'PaaS' },
  'Inventory forecasting': { icon: TrendingUp, service: 'PaaS' },
  'Conversational AI': { icon: MessageSquare, service: 'SaaS' },
  'Dynamic pricing intelligence': { icon: Tag, service: 'PaaS' },
  'Multi-tenant operations console': { icon: Building2, service: 'MaaS' },
  [BIDDING.title]: { icon: Gavel, service: 'PaaS' },
  [REVERSE_LOGISTICS.title]: { icon: Recycle, service: 'TaaS' },
  'Forecast-Triggered Surplus Auctions': { icon: Boxes, service: 'PaaS' },
  'Inter-Seller Stock Rebalancing': { icon: ArrowLeftRight, service: 'PaaS' },
  'Shelf-Life Decay Pricing': { icon: Timer, service: 'PaaS' },
  'Voice Counter-Offer Negotiation': { icon: Mic, service: 'SaaS' },
  'Carbon Impact Score per Offer': { icon: Leaf, service: 'TaaS' },
  'Snap-to-Bid Visual Search': { icon: Camera, service: 'SaaS' },
  'Return-Risk Guidance at Checkout': { icon: ShoppingCart, service: 'SaaS' },
  'Future Value Guarantee': { icon: Wallet, service: 'PaaS' },
  'Digital Product Passport': { icon: QrCode, service: 'PaaS' },
  'Predictive Trade-In Nudges': { icon: Bell, service: 'PaaS' },
  'Photo-Based AI Condition Grading': { icon: ScanLine, service: 'SaaS' },
  'Direct Peer Forwarding': { icon: Truck, service: 'TaaS' },
  'Refurbisher Capacity Matching': { icon: Wrench, service: 'TaaS' },
  'Parts Harvesting Marketplace': { icon: Puzzle, service: 'TaaS' },
  'Circular Green Credits': { icon: Award, service: 'MaaS' },
  'Live Circularity Scorecards': { icon: BarChart3, service: 'MaaS' },
  'Fair-Bid Guardrails': { icon: Scale, service: 'MaaS' },
  'Seller Trust Score': { icon: Star, service: 'MaaS' },
  'Explainable AI Decisions': { icon: Lightbulb, service: 'MaaS' },
  'Multilingual Voice Commerce': { icon: Languages, service: 'SaaS' },
  'Budget-Governed AI Serving': { icon: Gauge, service: 'MaaS' }
};

// Every feature, in one list: no groups, no categories
const ALL_FEATURES = (() => {
  const all = [
    ...CORE_CAPABILITIES.map((item) => ({ name: item.title, text: item.text })),
    { name: BIDDING.title, text: BIDDING.intro },
    { name: REVERSE_LOGISTICS.title, text: REVERSE_LOGISTICS.intro },
    ...LIFECYCLE_FEATURES.flatMap((group) => group.features.map((feature) => ({ name: feature.name, text: feature.text })))
  ];
  const seen = new Set();
  return all
    .filter((feature) => {
      const key = feature.name.trim().toLowerCase();
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .map((feature) => ({ ...feature, ...FEATURE_META[feature.name] }));
})();

const SERVICE_COLOUR = { MaaS: '#EA4335', PaaS: '#4285F4', TaaS: '#34A853', SaaS: '#FBBC04' };

// One service at a time: pick it, and its picture, pitch and capabilities slide in beside the picker
function ServiceExplorer() {
  const [code, setCode] = useState(SERVICES[1].code);
  const svc = SERVICES.find((x) => x.code === code);
  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      <div role="tablist" aria-label="Services" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
        {SERVICES.map((x) => {
          const on = x.code === code;
          return (
            <button key={x.code} role="tab" aria-selected={on} onClick={() => setCode(x.code)}
              className={`group flex items-center gap-4 rounded-2xl border p-4 text-left transition-all duration-300 ${on ? 'border-transparent bg-white shadow-xl ring-2' : 'border-google-gray-200 bg-white/70 hover:-translate-y-0.5 hover:bg-white hover:shadow-md'}`}
              style={on ? { '--tw-ring-color': SERVICE_COLOUR[x.code] } : undefined}>
              <span className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl transition-transform group-hover:scale-110 ${x.iconBox}`}><x.icon className="h-6 w-6" /></span>
              <span className="min-w-0 flex-1">
                <span className="block text-xs font-bold uppercase tracking-wider text-google-gray-500">{x.code}</span>
                <span className="block text-lg font-bold leading-tight text-google-teal-dark">{x.title}</span>
                <span className="block text-sm text-google-gray-600">{x.summary}</span>
              </span>
              <ArrowRight className={`h-5 w-5 shrink-0 transition-all ${on ? 'translate-x-0 text-google-teal opacity-100' : '-translate-x-2 opacity-0'}`} />
            </button>
          );
        })}
      </div>
      <div key={svc.code} role="tabpanel" className="animate-slide-left google-card overflow-hidden">
        <div className="h-1.5" style={{ background: `linear-gradient(90deg, ${SERVICE_COLOUR[svc.code]}, transparent)` }} />
        <div className="grid gap-5 p-5 sm:p-6 md:grid-cols-2">
          <img src={serviceImage(svc)} alt={`${svc.title} illustration`} loading="lazy" className="w-full rounded-xl border border-google-gray-100 bg-google-gray-50" />
          <div>
            <h3 className="mb-1 text-xl font-bold text-google-teal-dark">{svc.title}</h3>
            <p className="mb-4 text-sm text-google-gray-600">{SERVICE_PITCH[svc.code]}</p>
            <ul className="space-y-2.5">
              {svc.features.map((feature, i) => (
                <li key={feature} className="flex items-start gap-2 text-sm text-google-gray-800" style={{ animation: `fade-up .4s ${i * 60}ms both` }}>
                  <CheckCircle className="mt-0.5 h-4 w-4 shrink-0 text-google-teal" /><span>{feature}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

// Every feature, filterable by service and by a word in its name or text
function FeatureExplorer() {
  const [service, setService] = useState('all');
  const [q, setQ] = useState('');
  const shown = useMemo(() => ALL_FEATURES.filter((f) => (service === 'all' || f.service === service)
    && `${f.name} ${f.text}`.toLowerCase().includes(q.trim().toLowerCase())), [service, q]);
  return (
    <>
      <div className="mb-8 flex flex-col items-center gap-4">
        <label className="relative block w-full max-w-md">
          <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-google-gray-400" />
          <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search features, for example bidding or carbon" aria-label="Search features"
            className="w-full rounded-full border border-google-gray-300 bg-white py-2.5 pl-11 pr-10 text-sm shadow-sm focus:border-google-blue focus:outline-none focus:ring-4 focus:ring-google-blue/15" />
          {q && <button type="button" aria-label="Clear search" onClick={() => setQ('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-google-gray-400 hover:text-google-gray-700"><X className="h-4 w-4" /></button>}
        </label>
        <div className="flex flex-wrap justify-center gap-2" role="group" aria-label="Filter by service">
          {[{ code: 'all', label: 'All' }, ...SERVICES.map((x) => ({ code: x.code, label: x.code }))].map((c) => (
            <button key={c.code} type="button" onClick={() => setService(c.code)} aria-pressed={service === c.code}
              className={`rounded-full border px-4 py-1.5 text-sm font-semibold transition-all ${service === c.code ? 'google-btn-gradient border-transparent text-white shadow-md' : 'border-google-gray-300 bg-white text-google-gray-700 hover:border-google-blue hover:bg-google-blue-light/50'}`}>{c.label}</button>
          ))}
        </div>
      </div>
      {shown.length === 0 ? <p className="py-10 text-center text-google-gray-600">No features match that search.</p> : (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
          {shown.map((feature, i) => (
            <Reveal key={feature.name} delay={Math.min(i % 4, 3) * 70}>
              <div className="google-card lift group flex h-full flex-col p-6">
                <div className={`mb-4 w-fit rounded-xl p-3 transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-3 ${SERVICE_TILE[feature.service]}`}><feature.icon className="h-5 w-5" /></div>
                <div className="mb-1 text-[11px] font-bold uppercase tracking-wider text-google-gray-500">{feature.service}</div>
                <h4 className="mb-2 text-base font-bold text-google-teal-dark">{feature.name}</h4>
                <p className="text-sm leading-relaxed text-google-gray-600">{feature.text}</p>
              </div>
            </Reveal>
          ))}
        </div>
      )}
    </>
  );
}

const NAV = [['services', 'Services'], ['features', 'Features'], ['query', 'Contact']];

export default function LandingPage({ onOpenSignIn }) {
  const [scrolled, setScrolled] = useState(false);
  const scroller = useRef(null);
  useEffect(() => {
    const el = scroller.current;
    const on = () => setScrolled(el.scrollTop > 8);
    el?.addEventListener('scroll', on, { passive: true });
    return () => el?.removeEventListener('scroll', on);
  }, []);
  return (
    <div className="app-shell flex flex-col bg-white font-sans">
      <header className={`z-40 shrink-0 border-b bg-white/85 backdrop-blur-md transition-shadow ${scrolled ? 'border-google-gray-200 shadow-md' : 'border-transparent'}`}>
        <div className={SECTION}>
          <div className="flex h-16 items-center justify-between gap-4">
            <button type="button" onClick={() => scroller.current?.scrollTo({ top: 0, behavior: 'smooth' })} className="flex min-w-0 items-center gap-3" aria-label="Lakshmi, back to top">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl google-gradient-diag text-white shadow-sm sm:h-10 sm:w-10"><Sparkles className="h-5 w-5 sm:h-6 sm:w-6" /></div>
              <span className="whitespace-nowrap text-lg font-bold tracking-tight text-google-gray-900 sm:text-xl">Lakshmi</span>
            </button>
            <nav className="hidden items-center gap-1 md:flex" aria-label="Sections">
              {NAV.map(([id, label]) => <button key={id} type="button" onClick={() => scrollToId(id)} className="rounded-full px-4 py-2 text-sm font-medium text-google-gray-700 transition-colors hover:bg-google-blue-light hover:text-google-teal-dark">{label}</button>)}
            </nav>
            <button onClick={() => onOpenSignIn()} className="google-btn-primary shrink-0 whitespace-nowrap px-4 py-2 text-sm sm:px-6">
              <Lock className="h-4 w-4" />
              <span className="sm:hidden">Sign in</span>
              <span className="hidden sm:inline">Sign In to Platform</span>
            </button>
          </div>
        </div>
        <div className="h-1 google-gradient gradient-pan" />
      </header>

      <main id="app-scroll" ref={scroller} className="relative min-h-0 flex-1 overflow-y-auto">
        <HeroCarousel onOpenSignIn={onOpenSignIn} />

        {/* The platform in numbers */}
        <section className="relative z-10 -mt-1 bg-white">
          <div className={`${SECTION} py-8`}>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              {[[4, '', 'Connected services'], [ALL_FEATURES.length, '', 'Features'], [3, '', 'Portals: Owner, Consumer, Customer'], [400, '+', 'Platform APIs']].map(([n, suffix, text], i) => (
                <Reveal key={text} delay={i * 80}>
                  <div className="rounded-2xl border border-google-gray-200/70 bg-gradient-to-br from-google-blue-light/60 via-white to-google-green-light/60 p-5 text-center">
                    <div className="text-4xl font-extrabold text-google-teal"><Counter to={n} suffix={suffix} /></div>
                    <div className="mt-1 text-sm text-google-gray-600">{text}</div>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        <section id="services" className="scroll-mt-4 border-y border-google-gray-200/70 bg-gradient-to-b from-google-blue-light/50 via-white to-google-green-light/40">
          <div className={`${SECTION} py-20`}>
            <Reveal><SectionHeading center eyebrow="What we provide" title="Services" text="Four services, one connected platform. Pick one to see what it does." /></Reveal>
            <Reveal delay={100}><ServiceExplorer /></Reveal>
          </div>
        </section>

        <section id="features" className="scroll-mt-4 bg-white">
          <div className={`${SECTION} py-20`}>
            <Reveal><SectionHeading center eyebrow="What you get" title="Features" text="From first sale to final reuse, every stage of a product's life is covered." /></Reveal>
            <FeatureExplorer />
          </div>
        </section>

        <section id="query" className="scroll-mt-4 border-t border-google-gray-200/70 bg-gradient-to-br from-google-yellow-light/60 via-white to-google-blue-light/60">
          <div className={`${SECTION} py-16`}>
            <Reveal><SectionHeading eyebrow="Ask a query" title="Have a query? Contact us" text="Send your details and your question. We will reply by email, or give you a call." center /></Reveal>
            <Reveal delay={100}><QueryForm /></Reveal>
          </div>
        </section>

        <footer className="google-hero gradient-pan text-white">
          <div className={`${SECTION} flex flex-col items-center justify-between gap-4 py-8 text-sm sm:flex-row`}>
            <div><span className="font-bold">Lakshmi</span> • 360° Commerce Platform</div>
            <div className="flex items-center gap-4">
              {NAV.map(([id, label]) => <button key={id} type="button" onClick={() => scrollToId(id)} className="text-white/80 hover:text-white">{label}</button>)}
              <button type="button" onClick={() => onOpenSignIn()} className="rounded-lg border border-white/40 px-4 py-1.5 font-semibold hover:bg-white/15">Sign in</button>
            </div>
          </div>
          <div className="h-1 google-gradient" />
        </footer>
      </main>
    </div>
  );
}
