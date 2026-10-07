import React, { useState, useEffect } from 'react';
import { ShieldCheck, Users, Database, DollarSign, Activity, AlertTriangle, CheckCircle, Server } from 'lucide-react';
import LookerStudioEmbed from './LookerStudioEmbed';
import { getOverview } from './api';

export default function OwnerView() {
  const [health, setHealth] = useState(null);
  const [budget, setBudget] = useState(null);
  const [tenants, setTenants] = useState([]);
  const [users, setUsers] = useState([]);
  const [services, setServices] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const overview = await getOverview();
      setHealth(overview.health);
      setBudget(overview.budget);
      setTenants(overview.tenants);
      setUsers(overview.users);
      setServices(overview.services);
    } catch (err) {
      console.warn('API error, fallback to inline state:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="bg-gradient-to-r from-google-teal-dark via-google-teal to-google-blue rounded-2xl p-6 text-white shadow-sm">
        <div className="flex justify-between items-start">
          <div>
            <span className="inline-block px-3 py-1 bg-white/20 text-white rounded-full text-xs font-semibold mb-2 backdrop-blur-xs">
              MaaS — Management as a Service
            </span>
            <h1 className="text-2xl font-bold">Owner Operations & Security Console</h1>
            <p className="text-sm text-white/90 mt-1 max-w-2xl">
              Central management portal for operating services, enforcing tenant-scoped role access, monitoring multi-database infrastructure, and tracking GCP free-trial budget controls.
            </p>
          </div>
          <div className="bg-white/10 p-3 rounded-xl backdrop-blur-xs hidden md:block">
            <ShieldCheck className="h-10 w-10 text-white" />
          </div>
        </div>
      </div>

      {/* Operated Services (Owner controls all four) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { key: 'maas', label: 'MaaS', detail: services ? `${services.maas.tenants} tenants, ${services.maas.users} users` : '-' },
          { key: 'paas', label: 'PaaS', detail: services ? `${services.paas.products} products` : '-' },
          { key: 'taas', label: 'TaaS', detail: services ? `${services.taas.in_transit} of ${services.taas.shipments} shipments in transit` : '-' },
          { key: 'saas', label: 'SaaS', detail: services ? `${services.saas.open_tickets} open of ${services.saas.tickets} tickets` : '-' }
        ].map((svc) => (
          <div key={svc.key} className="google-card p-4">
            <div className="text-xs font-semibold uppercase tracking-wider text-google-gray-600">{svc.label}</div>
            <div className="text-sm font-semibold text-google-gray-900 mt-1">{svc.detail}</div>
          </div>
        ))}
      </div>

      {/* Looker Studio Analytics */}
      <LookerStudioEmbed />

      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="google-card p-5">
          <div className="flex justify-between items-center text-google-gray-600 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">3-Month Budget Cap</span>
            <DollarSign className="h-4 w-4 text-google-teal" />
          </div>
          <div className="text-2xl font-bold text-google-gray-900">${budget?.spent_to_date_usd || '18.45'}</div>
          <div className="text-xs text-google-gray-600 mt-1 flex items-center gap-1">
            <span>Limit: ${budget?.budget_limit_usd || '120.00'}</span>
            <span className="text-google-teal font-medium">({budget?.percentage_used || '15.3'}% used)</span>
          </div>
          <div className="w-full bg-google-gray-200 h-1.5 rounded-full mt-3 overflow-hidden">
            <div className="bg-google-teal h-full rounded-full" style={{ width: `${budget?.percentage_used || 15.3}%` }}></div>
          </div>
        </div>

        <div className="google-card p-5">
          <div className="flex justify-between items-center text-google-gray-600 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">System Health</span>
            <Activity className="h-4 w-4 text-google-green" />
          </div>
          <div className="text-2xl font-bold text-google-green flex items-center gap-2">
            <CheckCircle className="h-5 w-5" />
            <span>99.9% Online</span>
          </div>
          <p className="text-xs text-google-gray-600 mt-1">Cloud Run Scale-to-Zero Active</p>
        </div>

        <div className="google-card p-5">
          <div className="flex justify-between items-center text-google-gray-600 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Tenants</span>
            <Users className="h-4 w-4 text-google-blue" />
          </div>
          <div className="text-2xl font-bold text-google-gray-900">{tenants.length || 3}</div>
          <p className="text-xs text-google-gray-600 mt-1">Retailers, Refurbishers & Sellers</p>
        </div>

        <div className="google-card p-5">
          <div className="flex justify-between items-center text-google-gray-600 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">GCP Key Status</span>
            <Server className="h-4 w-4 text-google-yellow" />
          </div>
          <div className="text-lg font-bold text-google-teal">Keyless Preview</div>
          <p className="text-xs text-google-gray-600 mt-1">Mock Drivers Enabled</p>
        </div>
      </div>

      {/* Grid Section: Tenants & User Roles */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tenant Organisations */}
        <div className="google-card p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-lg text-google-gray-900 flex items-center gap-2">
              <Database className="h-5 w-5 text-google-teal" />
              <span>Multi-Tenant Organizations</span>
            </h3>
            <span className="google-pill bg-google-teal-surface text-google-teal">Row-Level Isolated</span>
          </div>
          <div className="divide-y divide-google-gray-200">
            {tenants.map((tenant) => (
              <div key={tenant.tenant_id} className="py-3 flex justify-between items-center">
                <div>
                  <div className="font-semibold text-google-gray-900 text-sm">{tenant.name}</div>
                  <div className="text-xs text-google-gray-600">{tenant.type} • ID: {tenant.tenant_id}</div>
                </div>
                <div className="text-right">
                  <span className="google-pill bg-google-green-light text-google-green font-medium">
                    {tenant.status}
                  </span>
                  <div className="text-xs text-google-gray-600 mt-0.5">{tenant.users_count} users</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* User Listing & RBAC Roles */}
        <div className="google-card p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-lg text-google-gray-900 flex items-center gap-2">
              <Users className="h-5 w-5 text-google-blue" />
              <span>User Listing & Role Access</span>
            </h3>
            <span className="google-pill bg-google-blue-light text-google-blue-dark">Firebase Auth</span>
          </div>
          <div className="divide-y divide-google-gray-200">
            {users.map((user) => (
              <div key={user.user_id} className="py-3 flex justify-between items-center">
                <div>
                  <div className="font-semibold text-google-gray-900 text-sm">{user.name}</div>
                  <div className="text-xs text-google-gray-600">{user.email}</div>
                </div>
                <div className="text-right">
                  <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-google-gray-100 text-google-gray-800">
                    {user.role}
                  </span>
                  <div className="text-xs text-google-teal mt-0.5">{user.tenant}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

