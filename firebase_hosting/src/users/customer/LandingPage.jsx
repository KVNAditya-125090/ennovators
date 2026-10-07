import React, { useState, useEffect } from 'react';
import {
  Sparkles, ShoppingBag, ShieldCheck, Truck, LifeBuoy, CheckCircle, Lock, ChevronLeft, ChevronRight
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

// Illustrations live in public/images
const BANNER_IMAGE = 'w-auto max-w-full h-[320px] sm:h-[400px] justify-self-center xl:justify-self-end rounded-2xl shadow-2xl bg-white';
// The overview picture has no card of its own, so it sits directly on the banner
const BANNER_IMAGE_BARE = 'w-auto max-w-full h-[340px] sm:h-[420px] justify-self-center xl:justify-self-end';
const serviceImage = (svc) => `/images/${svc.code.toLowerCase()}.svg`;

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
                  className={BANNER_IMAGE_BARE}
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

export default function LandingPage({ onOpenSignIn }) {
  return (
    <div className="app-shell bg-white flex flex-col font-sans">
      {/* Top Header */}
      <header className="shrink-0 bg-white border-b border-google-gray-200 z-40">
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

      <main id="app-scroll" className="relative flex-1 min-h-0 overflow-y-auto">
        {/* Hero carousel */}
        <HeroCarousel onOpenSignIn={onOpenSignIn} />

        {/* Services */}
        <section id="services" className="bg-google-gray-50 border-y border-google-gray-200">
          <div className={`${SECTION} py-20`}>
            <SectionHeading
              center
              eyebrow="What we provide"
              title="Services"
              text="Four services, one connected platform. Each can run on its own and works with the others through shared data."
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
                      <h4 className="font-bold text-lg text-google-gray-900 leading-tight">{svc.title}</h4>
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

        {/* Features */}
        <section id="features" className="bg-white">
          <div className={`${SECTION} py-20`}>
            <SectionHeading
              center
              eyebrow="What you get"
              title="Features"
              text="From first sale to final reuse, every stage of a product's life is covered."
            />

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
              {ALL_FEATURES.map((feature) => (
                <div key={feature.name} className="google-card p-6 flex flex-col">
                  <div className={`p-3 rounded-xl w-fit mb-4 ${SERVICE_TILE[feature.service]}`}>
                    <feature.icon className="h-5 w-5" />
                  </div>
                  <h4 className="font-bold text-base text-google-gray-900 mb-2">{feature.name}</h4>
                  <p className="text-sm text-google-gray-600 leading-relaxed">{feature.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Anyone can ask a question; the team replies by email or phone */}
        <section id="query" className="bg-google-gray-50 border-t border-google-gray-200">
          <div className={`${SECTION} py-16`}>
            <SectionHeading eyebrow="Ask a query" title="Have a query? Contact us" text="Send your details and your question. We will reply by email, or give you a call." center />
            <QueryForm />
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="shrink-0 bg-white border-t border-google-gray-200 py-8">
        <div className={`${SECTION} flex flex-col sm:flex-row justify-between items-center text-sm text-google-gray-600 gap-4`}>
          <div>
            <span className="font-bold text-google-teal">AuraCommerce 360</span> • Circular Commerce Platform
          </div>
        </div>
      </footer>
    </div>
  );
}
