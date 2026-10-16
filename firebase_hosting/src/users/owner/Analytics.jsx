import React, { useState, useEffect } from 'react';
import { BarChart3, Loader2, AlertCircle } from 'lucide-react';
import { getAnalytics } from './api';
import { LineChart } from './charts';

const PERIODS = [
  { key: '7d', label: '7 days' },
  { key: '30d', label: '30 days' },
  { key: '3m', label: '3 months' },
  { key: '6m', label: '6 months' },
  { key: '12m', label: '12 months' }
];

const METRIC_LABELS = { hosting: 'Budget', health: 'Health', consumers: 'Consumers', revenue: 'Revenue', support: 'Queries' };
const TARGET_SECONDS = 3;

const money = (v) => `$${Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const moneyAxis = (v) => `$${v >= 1000 ? `${(v / 1000).toFixed(v % 1000 === 0 ? 0 : 1)}k` : Number(v).toFixed(v < 10 && v % 1 !== 0 ? 2 : 0)}`;
const money$ = (v, exact) => (exact ? money(v) : moneyAxis(v));

// The history of whichever card is selected, as a plot. The cards above show the current values.
export default function Analytics({ metric }) {
  const [period, setPeriod] = useState('30d');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    getAnalytics(period)
      .then((result) => { if (!cancelled) setData(result); })
      .catch(() => { if (!cancelled) setError('Could not load the analytics. Please try again.'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [period]);

  const monthly = period === '12m';
  const parse = (iso) => new Date(`${iso}T00:00:00Z`);
  const formatX = (iso) => parse(iso).toLocaleDateString('en', monthly ? { month: 'short', year: '2-digit', timeZone: 'UTC' } : { month: 'short', day: 'numeric', timeZone: 'UTC' });
  const formatTip = (iso) => {
    const end = parse(iso).toLocaleDateString('en', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
    return period === '3m' || period === '6m' ? `Week ending ${end}` : monthly ? `Month ending ${end}` : end;
  };
  const periodLabel = PERIODS.find((p) => p.key === period).label;

  const plots = () => {
    const points = data.points;
    const common = { data: points, xKey: 'date', formatX, formatTip };

    if (metric === 'hosting') {
      return (
        <LineChart {...common} series={[{ key: 'hosting_cost', label: 'Budget', color: '#EA4335', area: true }]}
          formatY={money$} viewWidth={1200} height={260} ariaLabel={`Budget over the last ${periodLabel}`} />
      );
    }

    if (metric === 'revenue') {
      return (
        <LineChart {...common} series={[{ key: 'revenue', label: 'Revenue', color: '#34A853', area: true }]}
          formatY={money$} viewWidth={1200} height={260} ariaLabel={`Revenue over the last ${periodLabel}`} />
      );
    }

    if (metric === 'consumers') {
      const top = Math.max(...points.map((p) => p.consumers)) + 1;
      return (
        <LineChart {...common} series={[{ key: 'consumers', label: 'Consumers', color: '#4285F4', area: true }]}
          yMaxFixed={top} tickCount={top} formatY={(v) => String(Math.round(v))} viewWidth={1200} height={260} ariaLabel={`Consumers over the last ${periodLabel}`} />
      );
    }

    if (metric === 'support') {
      // running totals: small daily counts are noisy, and the gap between the lines is the backlog
      let openedSoFar = 0;
      let resolvedSoFar = 0;
      const running = points.map((p) => ({ date: p.date, opened: (openedSoFar += p.queries_received), resolved: (resolvedSoFar += p.queries_answered) }));
      const top = Math.max(4, Math.ceil((Math.max(openedSoFar, resolvedSoFar) * 1.1) / 4) * 4);
      return (
        <LineChart {...common} data={running}
          series={[{ key: 'opened', label: 'Received', color: '#EA4335' }, { key: 'resolved', label: 'Answered', color: '#34A853' }]}
          yMaxFixed={top} tickCount={4} formatY={(v) => String(Math.round(v))} viewWidth={1200} height={260} ariaLabel={`Queries received and answered over the last ${periodLabel}`} />
      );
    }

    // system health: three measures, each with its own scale
    const narrow = { viewWidth: 440, height: 220 };
    return (
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <div>
          <h3 className="text-sm font-semibold text-google-teal-dark mb-2">Uptime</h3>
          <LineChart {...common} {...narrow} series={[{ key: 'uptime_pct', label: 'Uptime', color: '#34A853', area: true }]}
            yMin={99.5} yMaxFixed={100} tickCount={5} formatY={(v) => `${Number(v).toFixed(2)}%`} ariaLabel="Uptime over time" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-google-teal-dark mb-2">Response time (p95)</h3>
          <LineChart {...common} {...narrow} series={[{ key: 'p95_seconds', label: 'Response time (p95)', color: '#F9AB00' }]}
            formatY={(v, exact) => (exact ? `${v}s` : `${Number(v).toFixed(1)}s`)} target={TARGET_SECONDS} targetLabel={`Target ${TARGET_SECONDS}s`} ariaLabel="Response time over time" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-google-teal-dark mb-2">Error rate</h3>
          <LineChart {...common} {...narrow} series={[{ key: 'errors_pct', label: 'Error rate', color: '#EA4335' }]}
            yMaxFixed={0.5} tickCount={5} formatY={(v) => `${Number(v).toFixed(2)}%`} ariaLabel="Error rate over time" />
        </div>
      </div>
    );
  };

  return (
    <div className="google-card p-6">
      <div className="flex flex-wrap justify-between items-center gap-4 mb-5">
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="font-bold text-lg text-google-teal-dark flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-google-teal" />
            <span>Analytics</span>
            <span className="font-normal text-google-gray-500">·</span>
            <span className="text-google-teal">{METRIC_LABELS[metric]}</span>
          </h2>
          {loading && data && <Loader2 className="h-4 w-4 animate-spin text-google-gray-500" />}
        </div>

        <div role="group" aria-label="Period" className="inline-flex rounded-lg border border-google-gray-300 bg-white p-0.5">
          {PERIODS.map((p) => (
            <button
              key={p.key}
              onClick={() => setPeriod(p.key)}
              aria-pressed={period === p.key}
              className={`px-3.5 py-1.5 rounded-md text-sm font-medium transition-colors ${
                period === p.key ? 'bg-google-blue text-white' : 'text-google-gray-700 hover:bg-google-gray-100'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div role="alert" className="flex items-center gap-2 rounded-xl bg-google-red-light text-google-red px-4 py-3 text-sm">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!data && loading && (
        <div className="flex items-center gap-2 text-sm text-google-gray-600 py-10"><Loader2 className="h-4 w-4 animate-spin" /> Loading...</div>
      )}

      {data && <div className={`transition-opacity ${loading ? 'opacity-60' : ''}`}>{plots()}</div>}
    </div>
  );
}
