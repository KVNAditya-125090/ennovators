import {
  Repeat, TrendingUp, MessageSquare, Tag, Building2,
  Boxes, ShoppingCart, QrCode, RotateCcw, Award, ShieldCheck, Globe,
  ShoppingBag, Wrench, Heart, Puzzle, Recycle
} from 'lucide-react';

// Source: AuraCommerce 360 Architecture & Solution Design Specification, section 7 (Features)

export const CORE_CAPABILITIES = [
  {
    icon: Repeat,
    title: 'End-to-end lifecycle management',
    text: 'A single digital record follows each product from supplier intake to disposal, giving every team a shared, real-time view.'
  },
  {
    icon: TrendingUp,
    title: 'Inventory forecasting',
    text: 'Demand forecasts per product and location drive reorder points, safety stock and allocation, reducing both stock-outs and overstock.'
  },
  {
    icon: MessageSquare,
    title: 'Conversational AI',
    text: 'An assistant supports voice and chat shopping, image-based product search, order tracking and guided returns in natural language.'
  },
  {
    icon: Tag,
    title: 'Dynamic pricing intelligence',
    text: 'AI estimates price elasticity and condition-adjusted value to inform bid floors and markdown decisions.'
  },
  {
    icon: Building2,
    title: 'Multi-tenant operations console',
    text: 'Retailers, sellers and refurbishers each manage catalog, bids and analytics within isolated, branded workspaces.'
  }
];

export const BIDDING = {
  title: 'Customer-to-Multi-Seller Bidding',
  intro: 'Instead of one seller setting a fixed price, a customer request triggers a short, bounded auction in which multiple eligible sellers compete.',
  steps: [
    { name: 'Intent capture', text: 'A voice or chat request becomes a structured demand: product, condition, budget and delivery window.' },
    { name: 'Seller matching', text: 'Eligible sellers are selected by stock, location, rating and condition grade.' },
    { name: 'Live bidding', text: 'Sellers submit offers in a live bid room, with price floors, ceilings and fairness rules enforced.' },
    { name: 'Best-fit award', text: 'Offers are ranked on price, delivery time, condition and seller reliability, and the winner is shown to the customer.' }
  ]
};

export const REVERSE_LOGISTICS = {
  title: 'Cradle-to-Cradle Reverse Logistics',
  intro: 'Returned and end-of-life goods become inputs to the next cycle, not waste. AI analyses return photos, predicts the grade and recovery value, and routes each item to the highest-value channel.',
  channels: [
    { name: 'Direct resale', icon: ShoppingBag },
    { name: 'Refurbishment', icon: Wrench },
    { name: 'Donation', icon: Heart },
    { name: 'Parts harvesting', icon: Puzzle },
    { name: 'Certified recycling', icon: Recycle }
  ],
  outro: 'Every decision is logged to support circularity metrics such as recovered value and landfill diversion rate.'
};

export const LIFECYCLE_FEATURES = [
  {
    stage: 'Supply & Inventory',
    icon: Boxes,
    features: [
      { name: 'Forecast-Triggered Surplus Auctions', text: 'When surplus is predicted for a product at a location, an auction opens before the stock ages, replacing late clearance markdowns.' },
      { name: 'Inter-Seller Stock Rebalancing', text: 'Forecast gaps between locations trigger transfer proposals, so one seller’s excess fills another’s predicted shortage.' },
      { name: 'Shelf-Life Decay Pricing', text: 'For perishable or seasonal goods, bid floors and prices decline automatically along the remaining shelf or season life.' }
    ]
  },
  {
    stage: 'Discovery & Purchase',
    icon: ShoppingCart,
    features: [
      { name: 'Voice Counter-Offer Negotiation', text: 'Customers counter a seller’s bid by voice or chat, and an AI agent bargains on their behalf within seller-approved guardrails.' },
      { name: 'Carbon Impact Score per Offer', text: 'Every bid shows an estimated carbon footprint, so customers can choose the greener offer.' },
      { name: 'Snap-to-Bid Visual Search', text: 'Photograph a product and the platform identifies it and opens a multi-seller bid for the same or an equivalent item.' },
      { name: 'Return-Risk Guidance at Checkout', text: 'The likelihood of a return is predicted, with size, fit or compatibility guidance before purchase.' },
      { name: 'Future Value Guarantee', text: 'At purchase, customers see a guaranteed buy-back or trade-in value for a future date.' }
    ]
  },
  {
    stage: 'Ownership',
    icon: QrCode,
    features: [
      { name: 'Digital Product Passport', text: 'A QR-linked record of origin, ownership, repairs, condition grades and carbon savings travels with each item across every resale.' },
      { name: 'Predictive Trade-In Nudges', text: 'The platform predicts when an item nears the end of its useful life and invites a trade-in bid while its value is still high.' }
    ]
  },
  {
    stage: 'Returns & Recovery',
    icon: RotateCcw,
    features: [
      { name: 'Photo-Based AI Condition Grading', text: 'Return photos are analysed and a condition grade and recovery value are assigned before the item is shipped anywhere.' },
      { name: 'Direct Peer Forwarding', text: 'A resaleable return is sold to the next buyer through a new bid and shipped directly from the returning customer, skipping the warehouse.' },
      { name: 'Refurbisher Capacity Matching', text: 'Items needing repair are matched to certified refurbishers by skill, capacity and location, and refurbishers bid for the work.' },
      { name: 'Parts Harvesting Marketplace', text: 'Items beyond repair are listed as component parts, so working modules are resold instead of recycled whole.' }
    ]
  },
  {
    stage: 'Loyalty & Impact',
    icon: Award,
    features: [
      { name: 'Circular Green Credits', text: 'Customers earn credits for trade-ins, responsible returns and choosing refurbished offers, redeemable across participating sellers.' },
      { name: 'Live Circularity Scorecards', text: 'Customers, sellers and retailers each see the value recovered, waste diverted and carbon saved by their own activity.' }
    ]
  },
  {
    stage: 'Trust & Safety',
    icon: ShieldCheck,
    features: [
      { name: 'Fair-Bid Guardrails', text: 'Price floors and ceilings, anomaly detection for collusion or manipulation, and human review for high-value awards keep auctions fair.' },
      { name: 'Seller Trust Score', text: 'A continuously updated score from delivery performance, grading accuracy and dispute history weights each seller’s bid ranking.' },
      { name: 'Explainable AI Decisions', text: 'Every price, bid award and recovery route comes with a plain-language reason showing the main factors behind it.' }
    ]
  },
  {
    stage: 'Platform',
    icon: Globe,
    features: [
      { name: 'Multilingual Voice Commerce', text: 'Voice and chat in multiple languages, including Indian languages, for inclusive shopping and returns.' },
      { name: 'Budget-Governed AI Serving', text: 'Per-tenant AI quotas, response caching and an automatic scale-down switch tied to spend budgets keep costs under control.' }
    ]
  }
];
