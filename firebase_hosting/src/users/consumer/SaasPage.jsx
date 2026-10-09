import React, { useState } from 'react';
import { Inbox, RotateCcw, Banknote, CalendarDays } from 'lucide-react';
import { useAllowedPages, useCurrentPage } from './consumerPages';
import { useConsumer, useLoad, useAction, Section, Empty, ErrorNote, FormModal, PageHeader, Kpi, Kpis, Avatar, DataTable, SearchBox, RowMenu, StatusSelect, Btn, Pill, label, money, FIELD } from './ui';
import { PageExtras } from './MoreFeatures';

// A ticket's conversation, with the one reply box and the status control
function Thread({ ticket, statuses, act }) {
  const { can, isRoot, userName } = useConsumer();
  const [reply, setReply] = useState('');
  const closed = ticket.status === 'closed';
  const send = async (e) => {
    e.preventDefault();
    if (await act.run('/saas/ticket/reply/staff/v1', { ticket_id: ticket.ticket_id, message: reply, author: userName }, 'Reply sent')) setReply('');
  };
  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="flex flex-wrap justify-between items-start gap-3 pb-3 border-b border-google-gray-200">
        <div className="flex items-center gap-3"><Avatar name={ticket.customer} /><div><div className="font-bold text-google-gray-900">{ticket.subject}</div><div className="text-sm text-google-gray-500">{ticket.ticket_id} • {ticket.customer}</div></div></div>
        <div className="flex items-center gap-2">
          {can('/saas/ticket/status/update/v1') && !closed
            ? <StatusSelect value={ticket.status} options={can('/saas/ticket/close/v1') ? statuses.filter((s) => s !== 'closed') : statuses} disabled={act.busy} onChange={(status) => act.run('/saas/ticket/status/update/v1', { ticket_id: ticket.ticket_id, status }, `Marked ${label(status).toLowerCase()}`)} />
            : <Pill value={ticket.status} />}
          <RowMenu items={[{ label: 'Close ticket', hidden: closed || !can('/saas/ticket/close/v1'), onClick: () => act.run('/saas/ticket/close/v1', { ticket_id: ticket.ticket_id }, 'Ticket closed') }]} />
        </div>
      </div>
      <div className="flex-1 min-h-0 overflow-y-auto flex flex-col gap-4 py-5 px-1">
        {ticket.messages.map((m, i) => {
          const staff = m.from === 'Staff';
          return (
            <div key={i} className={`flex flex-col gap-1 max-w-[75%] ${staff ? 'self-end items-end' : 'self-start items-start'}`}>
              {isRoot && staff && m.author && <span className="px-1 text-xs font-medium text-google-gray-500">{m.author}</span>}
              <div className={`w-fit whitespace-pre-wrap break-words px-4 py-2.5 text-base leading-relaxed shadow-sm ${staff ? 'rounded-2xl rounded-br-md bg-google-blue text-white' : 'rounded-2xl rounded-bl-md border border-google-gray-200 bg-white text-google-gray-900'}`}>
                {m.text}
              </div>
            </div>
          );
        })}
      </div>
      {can('/saas/ticket/reply/staff/v1') && !closed && (
        <form onSubmit={send} className="flex gap-2">
          <input className={FIELD} value={reply} onChange={(e) => setReply(e.target.value)} placeholder="Write a reply" aria-label="Reply" required />
          <Btn kind="primary" type="submit" disabled={act.busy} className="px-5">Send</Btn>
        </form>
      )}
    </div>
  );
}

function Tickets() {
  const { enumValues } = useConsumer();
  const { data, error, reload } = useLoad('/saas/ticket/read/staff/v1');
  const act = useAction(reload);
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState(null);
  const statuses = enumValues('/saas/ticket/status/update/v1', 'status');
  const tickets = data?.tickets ?? [];
  const q = query.trim().toLowerCase();
  const rows = tickets.filter((t) => (!q || `${t.subject} ${t.customer}`.toLowerCase().includes(q)));
  const selected = tickets.find((t) => t.ticket_id === selectedId) ?? rows[0];
  return (
    <div>
      <PageHeader title="Tickets" subtitle="Questions and problems from your customers" />
      <ErrorNote error={error || act.error} />
      <Section className="flex flex-col h-[calc(100vh-16rem)] min-h-[22rem]">
        <div className="grid lg:grid-cols-[24rem_1fr] gap-4 flex-1 min-h-0">
          <div className="flex flex-col min-h-0 gap-3">
            <SearchBox value={query} onChange={setQuery} placeholder="Search tickets" />
            <ul className="space-y-1 min-h-0 overflow-y-auto">
              {rows.map((t) => (
                <li key={t.ticket_id}>
                  <button onClick={() => setSelectedId(t.ticket_id)} aria-current={selected?.ticket_id === t.ticket_id}
                    className={`w-full flex gap-3 rounded-xl px-3 py-2.5 text-left transition-colors ${selected?.ticket_id === t.ticket_id ? 'bg-google-blue-light/60' : 'hover:bg-google-gray-50'}`}>
                    <Avatar name={t.customer} />
                    <span className="min-w-0 flex-1">
                      <span className="flex justify-between gap-2"><span className="text-base font-semibold text-google-gray-900 truncate">{t.subject}</span><Pill value={t.status} /></span>
                      <span className="block text-sm text-google-gray-500 truncate">{t.customer} • {t.messages.length} message{t.messages.length === 1 ? '' : 's'}</span>
                    </span>
                  </button>
                </li>
              ))}
              {rows.length === 0 && <Empty>{data ? 'No tickets match.' : 'Loading...'}</Empty>}
            </ul>
          </div>
          <div className="min-h-0 lg:border-l lg:border-google-gray-200 lg:pl-5">
            {selected ? <Thread key={selected.ticket_id} ticket={selected} statuses={statuses} act={act} /> : <Empty>Pick a ticket to read it.</Empty>}
          </div>
        </div>
      </Section>
    </div>
  );
}

function Returns() {
  const { can, enumValues } = useConsumer();
  const { data, error, reload } = useLoad('/saas/return/request/read/v1');
  const act = useAction(reload);
  const [dialog, setDialog] = useState(null); // { kind: 'reject' | 'refund' | 'policy', item }
  const open = (d) => { act.setError(''); setDialog(d); };
  const returns = data?.returns ?? [];
  const policy = data?.policy;
  const count = (s) => returns.filter((r) => r.status === s).length;
  const refunded = returns.filter((r) => r.status === 'refunded').reduce((n, r) => n + (r.refunded ?? r.amount), 0);
  const policyFields = [
    { name: 'window_days', label: 'Return window (days)', type: 'number', step: 1, required: true },
    { name: 'refund_method', label: 'Refund method', type: 'select', options: enumValues('/saas/return/policy/set/v1', 'refund_method'), required: true }
  ];
  return (
    <div>
      <PageHeader title="Returns and Refunds" subtitle="Decide what comes back and what you pay out"
        action={can('/saas/return/policy/set/v1') && policy && <Btn onClick={() => open({ kind: 'policy' })}>Return policy</Btn>} />
      <ErrorNote error={error || (!dialog && act.error)} />
      <Kpis>
        <Kpi icon={Inbox} tone="yellow" label="Waiting for your decision" value={count('requested')} />
        <Kpi icon={RotateCcw} tone="blue" label="Approved, to refund" value={count('approved')} />
        <Kpi icon={Banknote} tone="green" label="Refunded so far" value={money(refunded)} />
        {policy && <Kpi icon={CalendarDays} tone="teal" label="Return window" value={`${policy.window_days} days`} hint={`Refund to ${label(policy.refund_method).toLowerCase()} payment`} />}
      </Kpis>
      <Section title="Return requests">
        <DataTable rowKey={(r) => r.return_id} rows={returns} empty={data ? 'No return requests.' : 'Loading...'} columns={[
          { key: 'i', header: 'Return', render: (r) => <div className="flex items-center gap-3"><Avatar name={r.customer} /><div><div className="font-semibold text-google-gray-900">{r.item}</div><div className="text-sm text-google-gray-500">{r.return_id} • {r.customer}</div></div></div> },
          { key: 'w', header: 'Reason', render: (r) => <span className="text-google-gray-700">{r.reason}</span> },
          { key: 'a', header: 'Amount', render: (r) => <span className="font-semibold text-google-gray-900">{money(r.amount)}</span> },
          { key: 's', header: 'Status', render: (r) => <Pill value={r.status} /> },
          { key: 'x', header: '', className: 'text-right whitespace-nowrap', render: (r) => (
            <div className="inline-flex items-center justify-end gap-1">
              <span className="inline-block w-24">
                {r.status === 'requested' && can('/saas/return/request/approve/v1') && <Btn kind="primary" className="w-full justify-center" disabled={act.busy} onClick={() => act.run('/saas/return/request/approve/v1', { return_id: r.return_id }, 'Return approved')}>Approve</Btn>}
                {r.status === 'approved' && can('/saas/return/refund/issue/v1') && <Btn kind="primary" className="w-full justify-center" onClick={() => open({ kind: 'refund', item: r })}>Refund</Btn>}
              </span>
              <span className="inline-block w-8"><RowMenu items={[{ label: 'Reject', danger: true, hidden: r.status !== 'requested' || !can('/saas/return/request/reject/v1'), onClick: () => open({ kind: 'reject', item: r }) }]} /></span>
            </div>
          ) }
        ]} />
      </Section>
      {dialog?.kind === 'reject' && <FormModal title={`Reject ${dialog.item.return_id}`} fields={[{ name: 'reason', label: 'Reason shown to the customer', type: 'textarea', required: true }]} submitLabel="Reject return" error={act.error} busy={act.busy} onClose={() => setDialog(null)}
        onSubmit={async (v) => Boolean(await act.run('/saas/return/request/reject/v1', { ...v, return_id: dialog.item.return_id }, 'Return rejected'))} />}
      {dialog?.kind === 'refund' && <FormModal title={`Refund ${dialog.item.return_id}`} fields={[{ name: 'amount', label: 'Amount (USD)', type: 'number', required: true, hint: `Up to ${money(dialog.item.amount)}` }]} initial={{ amount: dialog.item.amount }} submitLabel="Issue refund" error={act.error} busy={act.busy} onClose={() => setDialog(null)}
        onSubmit={async (v) => Boolean(await act.run('/saas/return/refund/issue/v1', { ...v, return_id: dialog.item.return_id }, 'Refund issued'))} />}
      {dialog?.kind === 'policy' && <FormModal title="Return policy" fields={policyFields} initial={policy} error={act.error} busy={act.busy} onClose={() => setDialog(null)}
        onSubmit={async (v) => Boolean(await act.run('/saas/return/policy/set/v1', v, 'Policy saved'))} />}
    </div>
  );
}

export default function SaasPage() {
  const { can } = useConsumer();
  const pages = useAllowedPages('saas', can);
  const page = useCurrentPage('saas', pages);
  if (!page) return <Empty>Your workspace has not opted into any Support features.</Empty>;
  return (
    <div>
      {page === 'tickets' && <Tickets />}
      {page === 'returns' && <Returns />}
      <PageExtras service="saas" page={page} />
    </div>
  );
}
