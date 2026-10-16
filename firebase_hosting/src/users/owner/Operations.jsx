import React, { useEffect, useState } from 'react';
import FeatureCards from '../../services/features/FeatureCards';
import { getOwnerFeatures, runOwnerFeature } from './api';
import { PageTitle } from './Pages';
import { href } from '../../router';

// The Owner's own features from the catalog, one tab per area. All three Owner roles see all of them.
// They run in preview until the backend is integrated (cloud_run/preview.py, Owner router /features).
const TABS = [
  { key: 'onboarding', label: 'Onboarding', subtitle: 'Onboard consumers, provision their root account, grant or revoke endpoints and review opt-in requests',
    features: ['consumer', 'root-account', 'endpoint'] },
  { key: 'tickets', label: 'Consumer tickets', subtitle: 'Reply to and close the tickets consumers raise, and record agreed prices', features: ['owner-ticket'] },
  { key: 'partners', label: 'Partners', subtitle: 'Approve brokered partner links, set the commission policy and see partner usage', features: ['partner'] },
  { key: 'team', label: 'Owner team', subtitle: 'Owner roles (manager, developer, operator) and the mail ids that hold them', features: ['owner-role', 'owner-role-mail'] },
  { key: 'developer', label: 'Developer', subtitle: 'API keys for consumers, and endpoint versions', features: ['api-key', 'endpoint-version'] },
  { key: 'governance', label: 'Audit and impact', subtitle: 'The Owner-side audit log and how impact baselines are estimated', features: ['audit', 'impact'] },
  { key: 'account', label: 'Account', subtitle: 'Sign-in, sessions, invites and passwords for Owner accounts', features: ['owner-account'] }
];

export default function OperationsPage({ tab }) {
  const [features, setFeatures] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    getOwnerFeatures().then((d) => setFeatures(d.features)).catch(() => setError('Could not load the Owner features. Please try again.'));
  }, []);
  const current = TABS.find((t) => t.key === tab) ?? TABS[0];
  const list = (features ?? []).filter((e) => current.features.includes(e.feature));
  const count = (t) => (features ?? []).filter((e) => t.features.includes(e.feature)).length;

  return (
    <div className="space-y-4">
      <PageTitle title="Operations" subtitle="Everything the Owner runs on the platform side. All Owner roles see the same." />
      <div role="tablist" className="flex gap-1 border-b border-google-gray-200 overflow-x-auto">
        {TABS.map((t) => (
          <a key={t.key} role="tab" aria-selected={current.key === t.key} href={href(`maas/operations/${t.key}`)}
            className={`px-3 py-2 text-sm font-semibold whitespace-nowrap border-b-2 -mb-px ${current.key === t.key ? 'border-google-blue text-google-teal' : 'border-transparent text-google-gray-600 hover:text-google-gray-900'}`}>
            {t.label}{features && <span className="ml-1.5 font-normal text-google-gray-500">{count(t)}</span>}
          </a>
        ))}
      </div>
      {error && <div role="alert" className="rounded-lg bg-google-red-light text-google-red px-4 py-3 text-sm">{error}</div>}
      {!features && !error && <div className="text-sm text-google-gray-600">Loading...</div>}
      {features && (
        <>
          <p className="text-sm text-google-gray-600">{current.subtitle}.</p>
          <FeatureCards features={list} run={runOwnerFeature} title={null} />
        </>
      )}
    </div>
  );
}
