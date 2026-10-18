import React, { useState, useEffect, useCallback } from 'react';
import { Trash2 } from 'lucide-react';
import { Section, Dropdown, Empty, ErrorNote, FIELD, Pill, money, useToast } from '../consumer/ui';
import { AddressAutocomplete, mapsConfigured } from '../../maps';

// Cart, checkout, orders and wishlist on one screen. Each part shows only when the seller switched its feature on.
const P = {
  cartRead: '/paas/order/cart/read/v1', cartAdd: '/paas/order/cart/add/v1', cartRemove: '/paas/order/cart/remove/v1',
  checkout: '/paas/order/checkout/place/v1', coupon: '/paas/promotion/coupon/apply/v1',
  orders: '/paas/order/read/customer/v1', cancel: '/paas/order/cancel/customer/v1',
  wishRead: '/paas/wishlist/read/v1', wishRemove: '/paas/wishlist/item/remove/v1'
};
const PAYMENT = [['card', 'Card'], ['upi', 'UPI'], ['cod', 'Cash on delivery']];
const Btn = ({ danger, ...rest }) => <button type="button" {...rest} className={`rounded-lg border px-3 py-1 text-sm font-semibold disabled:opacity-60 ${danger ? 'border-google-red text-google-red hover:bg-google-red-light' : 'border-google-gray-300 text-google-gray-800 hover:bg-google-gray-50'}`} />;

export default function CartPage({ call, can }) {
  const toast = useToast();
  const [cart, setCart] = useState(null);
  const [orders, setOrders] = useState(null);
  const [wishlist, setWishlist] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [coupon, setCoupon] = useState({ code: '', applied: null });
  const [address, setAddress] = useState({ line1: '', city: '', postcode: '', country: '' });
  const [payment, setPayment] = useState('card');
  const [cancelling, setCancelling] = useState(null); // { id, reason }

  const reload = useCallback(async () => {
    try {
      if (can(P.cartRead)) setCart((await call(P.cartRead, {})).cart);
      if (can(P.orders)) setOrders((await call(P.orders, {})).orders);
      if (can(P.wishRead)) setWishlist((await call(P.wishRead, {})).wishlist);
    } catch (err) { setError(err.message); }
  }, [call, can]);
  useEffect(() => { reload(); }, [reload]);

  const act = async (key, path, params, done) => {
    setBusy(key); setError('');
    try { const data = await call(path, params); if (done) toast(done); await reload(); return data; }
    catch (err) { setError(err.message || 'The request failed.'); return null; }
    finally { setBusy(''); }
  };
  const applyCoupon = async (e) => {
    e.preventDefault();
    const data = await act('coupon', P.coupon, { code: coupon.code.trim() });
    if (data) setCoupon((c) => ({ ...c, applied: data }));
  };
  const place = async (e) => {
    e.preventDefault();
    const addr = Object.fromEntries(Object.entries(address).filter(([, v]) => v.trim()));
    if (!addr.line1 || !addr.city || !addr.postcode) { setError('Enter the street address, city and postcode to deliver to.'); return; }
    const data = await act('checkout', P.checkout, { address: addr, payment_method: payment, ...(coupon.applied ? { coupon_code: coupon.code.trim() } : {}) }, 'Order placed');
    if (data) setCoupon({ code: '', applied: null });
  };
  const setA = (k) => (e) => setAddress((a) => ({ ...a, [k]: e.target.value }));

  return (
    <div className="space-y-4">
      <ErrorNote error={error} />

      {can(P.cartRead) && (
        <Section title="Your cart" subtitle={cart ? `${cart.item_count} ${cart.item_count === 1 ? 'item' : 'items'}` : undefined}>
          {!cart ? <p className="text-sm text-google-gray-500">Loading...</p> : cart.lines.length === 0 ? <Empty>Your cart is empty. Add something from the Shop.</Empty> : (
            <>
              <ul className="divide-y divide-google-gray-100">
                {cart.lines.map((l) => (
                  <li key={l.product_id} className="flex items-center justify-between gap-3 py-3">
                    <div className="min-w-0">
                      <div className="font-semibold text-google-gray-900 break-words">{l.name}</div>
                      <div className="text-sm text-google-gray-500">{money(l.price)} × {l.quantity}</div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-semibold">{money(l.price * l.quantity)}</span>
                      {can(P.cartRemove) && <button type="button" aria-label={`Remove ${l.name} from cart`} disabled={busy === `rm${l.product_id}`} onClick={() => act(`rm${l.product_id}`, P.cartRemove, { product_id: l.product_id }, 'Removed from cart')} className="rounded-lg p-1.5 text-google-gray-500 hover:bg-google-red-light hover:text-google-red"><Trash2 className="h-4 w-4" /></button>}
                    </div>
                  </li>
                ))}
              </ul>
              <div className="mt-2 flex items-center justify-between border-t border-google-gray-200 pt-3 text-lg font-semibold"><span>Total</span><span>{money(cart.total_usd)}</span></div>

              {can(P.coupon) && (
                <form onSubmit={applyCoupon} className="mt-4 flex flex-wrap items-center gap-2">
                  <input className={`${FIELD} !w-48`} aria-label="Coupon code" placeholder="Coupon code" value={coupon.code} onChange={(e) => setCoupon({ code: e.target.value, applied: null })} />
                  <Btn onClick={applyCoupon} disabled={!coupon.code.trim() || busy === 'coupon'}>Apply</Btn>
                  {coupon.applied && <span className="text-sm font-medium text-google-green">{coupon.applied.discount_pct ? `${coupon.applied.discount_pct}% off with ${coupon.applied.code}` : 'Coupon applied'}</span>}
                </form>
              )}

              {can(P.checkout) && (
                <form onSubmit={place} className="mt-5 space-y-3 rounded-xl bg-google-gray-50 p-4">
                  <h4 className="text-base font-semibold text-google-gray-900">Checkout</h4>
                  <div className="grid gap-3 md:grid-cols-2">
                    {mapsConfigured() && (
                      <div className="md:col-span-2"><span className="mb-1 block text-sm font-semibold">Find your address</span>
                        <AddressAutocomplete placeholder="Start typing your address" onSelect={(p) => setAddress((a) => ({ line1: p.parts.line1 || p.address, city: p.parts.city || a.city, postcode: p.parts.postcode || a.postcode, country: p.parts.country || a.country }))} />
                      </div>
                    )}
                    <label className="block md:col-span-2"><span className="mb-1 block text-sm font-semibold">Street address</span><input className={FIELD} value={address.line1} onChange={setA('line1')} /></label>
                    <label className="block"><span className="mb-1 block text-sm font-semibold">City</span><input className={FIELD} value={address.city} onChange={setA('city')} /></label>
                    <label className="block"><span className="mb-1 block text-sm font-semibold">Postcode</span><input className={FIELD} value={address.postcode} onChange={setA('postcode')} /></label>
                    <label className="block"><span className="mb-1 block text-sm font-semibold">Country <span className="font-normal text-google-gray-500">(optional)</span></span><input className={FIELD} value={address.country} onChange={setA('country')} /></label>
                    <div><span className="mb-1 block text-sm font-semibold">Payment</span><Dropdown ariaLabel="Payment method" value={payment} onChange={setPayment} options={PAYMENT.map(([value, text]) => ({ value, label: text }))} /></div>
                  </div>
                  <button type="submit" disabled={busy === 'checkout'} className="inline-flex items-center rounded-lg google-btn-gradient px-5 py-2 text-sm font-semibold text-white disabled:opacity-60">{busy === 'checkout' ? 'Placing order...' : `Place order · ${money(cart.total_usd)}`}</button>
                </form>
              )}
            </>
          )}
        </Section>
      )}

      {can(P.orders) && (
        <Section title="Your orders">
          {!orders ? <p className="text-sm text-google-gray-500">Loading...</p> : orders.length === 0 ? <Empty>No orders yet.</Empty> : (
            <ul className="space-y-3">
              {orders.map((o) => (
                <li key={o.order_id} className="rounded-xl border border-google-gray-200 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div><div className="font-semibold text-google-gray-900">Order {String(o.order_id).slice(0, 8)}</div><div className="text-sm text-google-gray-500">Placed {o.placed_at}</div></div>
                    <div className="flex items-center gap-3"><Pill value={o.status} /><span className="font-semibold">{money(o.total_usd)}</span></div>
                  </div>
                  <ul className="mt-2 text-sm text-google-gray-700">{o.lines.map((l) => <li key={l.product_id}>{l.quantity} × {l.name}</li>)}</ul>
                  {o.status === 'cancelled' && o.cancel_reason && <p className="mt-1 text-sm text-google-gray-500">Reason: {o.cancel_reason}</p>}
                  {can(P.cancel) && o.status === 'placed' && (cancelling?.id === o.order_id ? (
                    <form className="mt-3 flex flex-wrap items-center gap-2" onSubmit={async (e) => { e.preventDefault(); if (await act(`c${o.order_id}`, P.cancel, { order_id: o.order_id, ...(cancelling.reason ? { reason: cancelling.reason } : {}) }, 'Order cancelled')) setCancelling(null); }}>
                      <input className={`${FIELD} !w-64`} aria-label="Reason for cancelling" placeholder="Reason (optional)" value={cancelling.reason} onChange={(e) => setCancelling({ id: o.order_id, reason: e.target.value })} />
                      <Btn danger onClick={() => act(`c${o.order_id}`, P.cancel, { order_id: o.order_id, ...(cancelling.reason ? { reason: cancelling.reason } : {}) }, 'Order cancelled').then((d) => d && setCancelling(null))}>Yes, cancel order</Btn>
                      <Btn onClick={() => setCancelling(null)}>Keep order</Btn>
                    </form>
                  ) : <div className="mt-3"><Btn danger onClick={() => setCancelling({ id: o.order_id, reason: '' })}>Cancel order</Btn></div>)}
                </li>
              ))}
            </ul>
          )}
        </Section>
      )}

      {can(P.wishRead) && (
        <Section title="Wishlist">
          {!wishlist ? <p className="text-sm text-google-gray-500">Loading...</p> : wishlist.length === 0 ? <Empty>Nothing saved yet. Tap the heart on a product in the Shop.</Empty> : (
            <ul className="divide-y divide-google-gray-100">
              {wishlist.map((w) => (
                <li key={w.product_id} className="flex items-center justify-between gap-3 py-3">
                  <div className="min-w-0"><div className="font-semibold text-google-gray-900 break-words">{w.name}</div><div className="text-sm text-google-gray-500">{money(w.price)}</div></div>
                  <div className="flex gap-2">
                    {can(P.cartAdd) && <Btn disabled={busy === `a${w.product_id}`} onClick={() => act(`a${w.product_id}`, P.cartAdd, { product_id: w.product_id, quantity: 1 }, 'Added to cart')}>Add to cart</Btn>}
                    {can(P.wishRemove) && <Btn onClick={() => act(`w${w.product_id}`, P.wishRemove, { product_id: w.product_id }, 'Removed from wishlist')}>Remove</Btn>}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Section>
      )}
    </div>
  );
}
