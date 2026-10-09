import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { getDashboard, loadOpted, callEndpoint } from './api';
import { ConsumerContext, ToastProvider } from './ui';
import { useRoute } from './consumerPages';
import MaasPage from './MaasPage';
import PaasPage from './PaasPage';
import TaasPage from './TaasPage';
import SaasPage from './SaasPage';

const PAGES = { maas: MaasPage, paas: PaasPage, taas: TaasPage, saas: SaasPage };

export default function ConsumerView({ tenant, isRoot, user }) {
  const [workspace, setWorkspace] = useState(null);
  const [endpoints, setEndpoints] = useState(null); // {path: endpoint}: only what this workspace has opted into
  const [failed, setFailed] = useState(false);
  const { service: section, feature } = useRoute();

  // an address that names a feature (…/<page>/<feature>) scrolls to that feature's card once the page has drawn it
  useEffect(() => {
    if (!feature || !endpoints) return undefined;
    const prefix = `/${section}/${feature}/`;
    let tries = 0;
    const timer = window.setInterval(() => {
      const card = [...document.querySelectorAll('[data-endpoint]')].find((el) => el.dataset.endpoint.startsWith(prefix));
      if (card || ++tries > 20) window.clearInterval(timer);
      if (!card) return;
      card.scrollIntoView({ block: 'center', behavior: 'smooth' });
      card.classList.add('bg-google-teal-surface');
      window.setTimeout(() => card.classList.remove('bg-google-teal-surface'), 2000);
    }, 150);
    return () => window.clearInterval(timer);
  }, [section, feature, endpoints]);

  useEffect(() => {
    getDashboard('SKU-WATCH-G3', tenant)
      .then((dashboard) => setWorkspace(dashboard.workspace))
      .catch(() => setFailed(true));
    loadOpted(tenant, user?.email).then(setEndpoints).catch(() => setFailed(true));
  }, [tenant, user?.email]);

  const tenantId = workspace?.tenant?.tenant_id;
  const can = useCallback((path) => Boolean(endpoints && endpoints[path]), [endpoints]);
  const call = useCallback((path, params) => {
    if (!endpoints?.[path]) return Promise.reject(new Error('Your workspace has not opted into this feature.'));
    return callEndpoint(tenantId, endpoints[path], params, user);
  }, [endpoints, tenantId, user]);
  const enumValues = useCallback((path, name) => endpoints?.[path]?.parameters.find((p) => p.name === name)?.values ?? [], [endpoints]);
  const userName = user?.name;
  const context = useMemo(() => ({ can, call, enumValues, workspace, tenantId, endpoints, isRoot, userName }), [can, call, enumValues, workspace, tenantId, endpoints, isRoot, userName]);

  const Page = PAGES[section];
  if (failed) return <div className="text-base text-google-red">Could not load your workspace. Check that the platform is running and try again.</div>;
  if (!endpoints || !tenantId) return <div className="text-base text-google-gray-600">Loading your workspace...</div>;
  return (
    <ConsumerContext.Provider value={context}>
      <ToastProvider>
        <Page key={section} />
      </ToastProvider>
    </ConsumerContext.Provider>
  );
}
