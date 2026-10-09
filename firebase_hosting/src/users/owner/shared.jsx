import React from 'react';

// What the Owner pages share: the endpoint status dot and the colours for priorities and statuses
export const ENDPOINT_STATUS = {
  active: { label: 'Active', color: '#34A853' },
  slow: { label: 'Late response', color: '#FBBC04' },
  failing: { label: 'Failing', color: '#EA4335' },
  stopped: { label: 'Stopped', color: '#9AA0A6' },
  not_built: { label: 'Not built yet', color: '#DADCE0' }
};
// The state the API reports for an endpoint (cloud_run/health.py), as shown here
export const HEALTH_STATE = { working: 'active', slow: 'slow', failing: 'failing', not_built: 'not_built' };

// A glowing dot; with `showLabel` the status is written next to it
export function EndpointStatus({ status, latency, showLabel = false }) {
  const s = ENDPOINT_STATUS[status] || ENDPOINT_STATUS.stopped;
  const text = latency ? `${s.label}, ${latency.toLocaleString()} ms` : s.label;
  return (
    <span className="inline-flex items-center gap-2" title={text}>
      <span
        role="img"
        aria-label={`Endpoint status: ${text}`}
        className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
        style={{ backgroundColor: s.color, boxShadow: `0 0 0 3px ${s.color}33, 0 0 8px ${s.color}` }}
      />
      {showLabel && <span className="font-semibold text-google-gray-700">{s.label}</span>}
    </span>
  );
}

export const PRIORITY_PILLS = { High: 'bg-google-red-light text-google-red', Normal: 'bg-google-blue-light text-google-blue-dark', Low: 'bg-google-gray-100 text-google-gray-600' };
export const QUERY_PILLS = { New: 'bg-google-yellow-light text-google-gray-900', 'In conversation': 'bg-google-blue-light text-google-blue-dark', Closed: 'bg-google-green-light text-google-green' };
export const QUERY_STATUS_PILLS = { Open: 'bg-google-yellow-light text-google-gray-900', 'In progress': 'bg-google-blue-light text-google-blue-dark', Resolved: 'bg-google-green-light text-google-green' };

export const formatDay = (iso) => new Date(`${iso}T00:00:00`).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

// An on/off switch
export function Switch({ checked, disabled, onChange, label }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 rounded-full transition-colors disabled:opacity-60 ${checked ? 'bg-google-green' : 'bg-google-gray-300'}`}
    >
      <span className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-5' : ''}`} />
    </button>
  );
}
