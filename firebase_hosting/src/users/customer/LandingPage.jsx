import React, { useState, useEffect } from 'react';
import {
  Sparkles, ShoppingBag, ShieldCheck, Gavel, Truck, LifeBuoy, CheckCircle, Lock,
  Package, Recycle, Camera, TrendingUp, MessageSquare, Server, Flame, BarChart3,
  Database, HardDrive, Cpu, Cloud, Layers, ChevronLeft, ChevronRight
} from 'lucide-react';

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
      'Multi-tenant management and user listing',
      'Live system health across Cloud Run, Firebase Auth, Vertex AI and Cloud SQL',
      'GCP budget tracking with alerts and a kill switch at the cap',
      'Looker Studio analytics on BigQuery data'
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
      'TimesFM demand forecasting with reorder points',
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
      'Gemini Flash AI shopping and support assistant',
      'Photo-based return grading with recovery estimate and recommended channel',
      'Secure return photo upload to Cloud Storage',
      'Support ticket tracking with priority and status',
      'After-sales and warranty handling'
    ]
  }
];

const JOURNEY = [
  { icon: Package, title: 'List', text: 'Sellers publish new, refurbished and open-box products with condition grades.' },
  { icon: Gavel, title: 'Bid', text: 'Customers post a budget and certified sellers compete in a live bidding room.' },
  { icon: Truck, title: 'Deliver', text: 'Shipments are tracked end to end with carrier, ETA and CO2 saved.' },
  { icon: Camera, title: 'Return', text: 'A photo is graded by AI for condition and recovery value in seconds.' },
  { icon: Recycle, title: 'Reuse', text: 'Each item is routed to resale, refurbishment or recycling, so little is wasted.' }
];

const INTELLIGENCE = [
  {
    icon: MessageSquare,
    title: 'Gemini Flash assistant',
    text: 'A conversational assistant for shopping, bids, returns and support questions, with suggested next actions.',
    chips: ['Product search', 'Bid help', 'Return start']
  },
  {
    icon: TrendingUp,
    title: 'TimesFM demand forecasting',
    text: 'Zero-shot time series forecasts built on BigQuery sales history, with a recommended reorder point per SKU.',
    chips: ['14-day outlook', 'Reorder point', 'Confidence range']
  },
  {
    icon: Camera,
    title: 'Photo return grading',
    text: 'Vision grading assigns a condition grade, predicts recovery value and recommends the best channel.',
    chips: ['Grade A to C', 'Recovery %', 'Channel routing']
  }
];

const STACK = [
  { icon: Cloud, name: 'Firebase Hosting', text: 'Serves the web app and routes API calls' },
  { icon: BarChart3, name: 'Looker Studio', text: 'Owner analytics dashboards' },
  { icon: Server, name: 'Cloud Run', text: 'Serverless API for all four services' },
  { icon: Cpu, name: 'Vertex AI', text: 'Gemini Flash, TimesFM and TabFM' },
  { icon: Layers, name: 'BigQuery', text: 'Sales history and spend analytics' },
  { icon: Database, name: 'Cloud SQL', text: 'Tenants, users and roles' },
  { icon: Flame, name: 'Firestore', text: 'Products, shipments and tickets' },
  { icon: HardDrive, name: 'Cloud Storage', text: 'Return photos and media' }
];

const SECTION = 'w-full px-4 sm:px-8 lg:px-12 2xl:px-20';

// Illustrations live in public/images
const BANNER_IMAGE = 'w-auto max-w-full h-[320px] sm:h-[400px] justify-self-center xl:justify-self-end rounded-2xl shadow-2xl bg-white';
const serviceImage = (svc) => `/images/${svc.code.toLowerCase()}.svg`;

const SERVICE_PITCH = {
  MaaS: 'Run the whole platform with confidence: who can do what, how it is performing and what it costs.',
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
      className="google-hero text-white relative overflow-hidden flex flex-col"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <div className="absolute -top-24 -right-24 h-96 w-96 rounded-full bg-google-yellow/20" />
      <div className="absolute -bottom-32 left-1/3 h-80 w-80 rounded-full bg-google-red/20" />

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
                  <span className="inline-block px-3.5 py-1 bg-white/15 rounded-full text-xs font-semibold">
                    Built on Google Cloud serverless
                  </span>
                  <h1 className="text-3xl sm:text-4xl 2xl:text-5xl font-extrabold tracking-tight leading-tight">
                    Intelligent 360° <span className="google-gradient-text-light">circular commerce</span>, from first sale to final reuse
                  </h1>
                  <p className="text-lg text-white/85 leading-relaxed max-w-2xl">
                    Unify sourcing, inventory forecasting, multi-seller bidding, delivery and AI-driven returns in one connected platform, so every product gets a second life.
                  </p>
                </div>
                <img
                  src="/images/overview.svg"
                  alt="The AuraCommerce web app: storefront with live bidding, shipment tracking, AI assistant and return grading"
                  className={BANNER_IMAGE}
                />
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
                      <span className="google-gradient-text-light">{svc.title}</span>
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
      <h2 className="text-3xl sm:text-4xl font-bold text-google-gray-900 tracking-tight">{title}</h2>
      {text && <p className="mt-3 text-base text-google-gray-600 leading-relaxed">{text}</p>}
    </div>
  );
}

export default function LandingPage({ onOpenSignIn }) {
  return (
    <div className="min-h-screen bg-white flex flex-col font-sans">
      {/* Top Header */}
      <header className="bg-white/95 backdrop-blur-sm border-b border-google-gray-200 sticky top-0 z-40">
        <div className={SECTION}>
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="h-10 w-10 rounded-xl google-gradient-diag flex items-center justify-center text-white shadow-sm">
                <Sparkles className="h-6 w-6" />
              </div>
              <span className="font-bold text-xl text-google-gray-900 tracking-tight">AuraCommerce 360</span>
            </div>

            <button onClick={() => onOpenSignIn()} className="google-btn-primary px-6 py-2 text-sm">
              <Lock className="h-4 w-4" />
              <span>Sign In to Platform</span>
            </button>
          </div>
        </div>
        <div className="h-1 google-gradient" />
      </header>

      <main>
        {/* Hero carousel */}
        <HeroCarousel onOpenSignIn={onOpenSignIn} />

        {/* Journey */}
        <section id="journey" className="bg-white">
          <div className={`${SECTION} py-20`}>
            <SectionHeading
              center
              eyebrow="How it works"
              title="The circular journey of every product"
              text="Five connected steps keep products in use longer and cut waste."
            />
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-6">
              {JOURNEY.map((step, index) => (
                <div key={step.title} className="google-card p-6 relative">
                  <div className="flex items-center justify-between mb-4">
                    <div className="p-3 bg-google-teal-surface text-google-teal rounded-xl">
                      <step.icon className="h-6 w-6" />
                    </div>
                    <span className="text-3xl font-extrabold text-google-gray-200">{String(index + 1).padStart(2, '0')}</span>
                  </div>
                  <h3 className="font-bold text-lg mb-2">{step.title}</h3>
                  <p className="text-sm text-google-gray-600 leading-relaxed">{step.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Services */}
        <section id="services" className="bg-google-gray-50 border-y border-google-gray-200">
          <div className={`${SECTION} py-20`}>
            <SectionHeading
              eyebrow="Platform services"
              title="Four services, one connected platform"
              text="Each service can be operated on its own and works with the others through shared data."
            />
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
              {SERVICES.map((svc) => (
                <div key={svc.code} className={`google-card p-6 border-t-4 ${svc.accent}`}>
                  <img src={serviceImage(svc)} alt={`${svc.title} illustration`} loading="lazy" className="w-full h-auto rounded-xl mb-5 border border-google-gray-100" />
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`p-3 rounded-xl w-fit ${svc.iconBox}`}>
                      <svc.icon className="h-6 w-6" />
                    </div>
                    <div>
                      <div className="text-xs font-bold uppercase tracking-wider text-google-gray-600">{svc.code}</div>
                      <h3 className="font-bold text-lg text-google-gray-900 leading-tight">{svc.title}</h3>
                    </div>
                  </div>
                  <p className="text-sm text-google-gray-600 mb-4">{svc.summary}</p>
                  <ul className="space-y-2">
                    {svc.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-2 text-sm text-google-gray-800">
                        <CheckCircle className="h-4 w-4 mt-0.5 shrink-0 text-google-teal" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Intelligence */}
        <section id="intelligence" className="bg-white">
          <div className={`${SECTION} py-20`}>
            <SectionHeading
              center
              eyebrow="Intelligence"
              title="AI built into every step"
              text="Vertex AI models assist shoppers, sellers and operators without extra tools."
            />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {INTELLIGENCE.map((item) => (
                <div key={item.title} className="google-card p-8">
                  <div className="p-3 bg-google-blue-light text-google-blue rounded-xl w-fit mb-5">
                    <item.icon className="h-7 w-7" />
                  </div>
                  <h3 className="font-bold text-xl mb-2">{item.title}</h3>
                  <p className="text-sm text-google-gray-600 leading-relaxed mb-5">{item.text}</p>
                  <div className="flex flex-wrap gap-2">
                    {item.chips.map((chip) => (
                      <span key={chip} className="google-pill bg-google-gray-100 text-google-gray-800">{chip}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Platform / Google Cloud stack */}
        <section id="platform" className="bg-white">
          <div className={`${SECTION} py-20`}>
            <SectionHeading
              center
              eyebrow="Platform"
              title="Built on Google Cloud"
              text="Serverless services that scale to zero when idle and grow with demand."
            />
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6">
              {STACK.map((item) => (
                <div key={item.name} className="google-card p-6 flex items-start gap-4">
                  <div className="p-3 bg-google-gray-100 text-google-teal rounded-xl shrink-0">
                    <item.icon className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base">{item.name}</h3>
                    <p className="text-sm text-google-gray-600 mt-1">{item.text}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-google-gray-200 py-8">
        <div className={`${SECTION} flex flex-col sm:flex-row justify-between items-center text-sm text-google-gray-600 gap-4`}>
          <div>
            <span className="font-bold text-google-teal">AuraCommerce 360</span> • GCP Circular Commerce Platform
          </div>
        </div>
      </footer>
    </div>
  );
}
