import React from 'react';
import FeatureCards from '../../services/features/FeatureCards';
import { PAGE_FEATURES } from './featureCatalog';
import { SERVICES } from './consumerPages';
import { useConsumer, PageHeader } from './ui';

// The catalog features that belong on a page but have no screen of their own yet, as runnable cards.
// Only the ones this workspace opted into and this person's role allows are shown.
export function MoreFeatures({ service, page, title }) {
  const { endpoints, call } = useConsumer();
  const features = (PAGE_FEATURES[`${service}/${page}`] ?? []).map((path) => endpoints[path]).filter(Boolean);
  return <FeatureCards features={features} title={title} run={(e, params) => call(e.path, params)} />;
}

// A page made only of feature cards
export function FeaturesPage({ service, page }) {
  const info = SERVICES.find((s) => s.key === service)?.pages.find((p) => p.key === page);
  return (
    <div>
      <PageHeader title={info?.label} subtitle={info?.subtitle} />
      <MoreFeatures service={service} page={page} title="Actions" />
    </div>
  );
}

// What a service page renders under its own screens: feature cards, or a whole page of them
export function PageExtras({ service, page }) {
  const info = SERVICES.find((s) => s.key === service)?.pages.find((p) => p.key === page);
  return info?.subtitle ? <FeaturesPage service={service} page={page} /> : <MoreFeatures service={service} page={page} />;
}
