import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Search, CornerDownLeft, FileText, Zap } from 'lucide-react';
import { SERVICES, availablePages, pageForPath, pageId, featureRest } from './consumerPages';
import { href, navigate } from '../../router';
import { SERVICE_LOOK } from './ui';

const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;

// Ctrl+K (or Cmd+K): type what you want to do and jump straight to the page that does it.
export default function CommandPalette({ opted, view, onClose }) {
  const [query, setQuery] = useState('');
  const [cursor, setCursor] = useState(0);
  const listRef = useRef(null);
  const can = (path) => Boolean(opted[path]);

  // everything that can be opened: the pages, then every feature that lives on one of them
  const all = useMemo(() => {
    const items = [];
    const pageLabel = {};
    SERVICES.forEach((svc) => availablePages(svc.key, can, view).forEach((p) => {
      pageLabel[pageId(svc.key, p.key)] = p.label;
      items.push({ kind: 'page', key: pageId(svc.key, p.key), label: p.label, sub: svc.label, service: svc.key, href: href(`${svc.key}/${p.key}`) });
    }));
    Object.values(opted).forEach((e) => {
      const target = pageForPath(e.path);
      if (!target) return;
      const id = pageId(target.service, target.page);
      if (!pageLabel[id]) return; // that page is not available here
      items.push({ kind: 'feature', key: e.path, label: e.description, sub: `${SERVICES.find((s) => s.key === target.service).label} • ${pageLabel[id]}`, service: target.service, href: href(featureRest(target.service, target.page, e.path)), extra: e.path });
    });
    return items;
  }, [opted, view]); // eslint-disable-line react-hooks/exhaustive-deps

  const results = useMemo(() => {
    const words = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
    const hits = all.filter((i) => words.every((w) => `${i.label} ${i.sub} ${i.extra ?? ''}`.toLowerCase().includes(w)));
    return hits.slice(0, 40);
  }, [all, query]);

  useEffect(() => { setCursor(0); }, [query]);
  useEffect(() => { listRef.current?.querySelector('[aria-selected="true"]')?.scrollIntoView({ block: 'nearest' }); }, [cursor]);

  const go = (item) => { navigate(item.href); onClose(); };
  const onKey = (e) => {
    if (e.key === 'Escape') onClose();
    else if (e.key === 'ArrowDown') { e.preventDefault(); setCursor((c) => Math.min(c + 1, results.length - 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setCursor((c) => Math.max(c - 1, 0)); }
    else if (e.key === 'Enter' && results[cursor]) go(results[cursor]);
  };

  return (
    <div className="fixed inset-0 z-[80] flex items-start justify-center bg-black/40 px-4 pt-[12vh]" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div role="dialog" aria-modal="true" aria-label="Search" className="w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-2xl">
        <div className="flex items-center gap-3 border-b border-google-gray-200 px-4">
          <Search className="h-5 w-5 text-google-gray-400" />
          <input autoFocus value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={onKey} placeholder="Search pages and features, for example refund, stock or invite"
            aria-label="Search" className="h-14 flex-1 bg-transparent text-lg text-google-gray-900 outline-none placeholder:text-google-gray-400" />
          <kbd className="rounded-md border border-google-gray-200 px-1.5 py-0.5 text-xs text-google-gray-500">Esc</kbd>
        </div>
        <ul ref={listRef} role="listbox" className="max-h-[50vh] overflow-y-auto p-2">
          {results.map((item, i) => {
            const look = SERVICE_LOOK[item.service];
            const Icon = item.kind === 'page' ? FileText : Zap;
            return (
              <li key={`${item.kind}-${item.key}`} role="option" aria-selected={i === cursor}>
                <button onClick={() => go(item)} onMouseMove={() => setCursor(i)}
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left ${i === cursor ? 'bg-google-gray-100' : ''}`}>
                  <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${look.tint}`}><Icon className="h-4 w-4" /></span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-base text-google-gray-900">{item.label}</span>
                    <span className="block truncate text-sm text-google-gray-500">{item.kind === 'page' ? `Page • ${item.sub}` : item.sub}</span>
                  </span>
                  {i === cursor && <CornerDownLeft className="h-4 w-4 text-google-gray-400" />}
                </button>
              </li>
            );
          })}
          {results.length === 0 && <li className="px-4 py-10 text-center text-base text-google-gray-500">Nothing matches "{query}".</li>}
        </ul>
        <div className="flex items-center justify-between border-t border-google-gray-100 px-4 py-2 text-xs text-google-gray-500">
          <span>{plural(all.filter((i) => i.kind === 'feature').length, 'feature')} on {plural(all.filter((i) => i.kind === 'page').length, 'page')}</span>
          <span>Up and down to move, Enter to open</span>
        </div>
      </div>
    </div>
  );
}
