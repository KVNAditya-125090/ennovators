import React from 'react';

// What the Owner pages share: the endpoint status dot and the colours for priorities and statuses
export const ENDPOINT_STATUS = {
  active: { label: 'Active', color: '#34A853' },
  slow: { label: 'Late response', color: '#FBBC04' },
  failing: { label: 'Failing', color: '#EA4335' },
  stopped: { label: 'Stopped', color: '#9AA0A6' }
};

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
