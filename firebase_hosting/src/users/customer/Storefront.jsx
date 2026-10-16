import React, { useState, useEffect } from 'react';
import { ShoppingCart, Gavel, Heart, QrCode, Leaf, Star, Sparkles, Play, Image as ImageIcon } from 'lucide-react';
import { getStorefront } from './api';
import { Section, Empty, useToast, SearchBox, Chips, Dropdown, Drawer } from '../consumer/ui';
import ResultView from './Results';

// The shop screen: the consumer's products, each with the real actions a shopper has (add to cart, wishlist,
// start a bid, open the passport). Calls go through the gate like every other feature; the rest of the Shop
// page's features are listed below this as runnable cards.
// A product's pictures and videos: the cover first, a strip to pick another picture, and a button to watch a video.
function ProductMedia({ product, layout }) {
  const pictures = product.images?.length ? product.images : [product.image_url].filter(Boolean);
  const videos = product.videos ?? [];
  const [index, setIndex] = useState(0);
  const [watching, setWatching] = useState(-1);
  const frame = layout === 'list' ? 'h-full w-48 min-h-[11rem]' : 'w-full h-44';
  return (
    <div className="relative shrink-0 overflow-hidden">
      {watching >= 0
        ? <video key={videos[watching]} src={videos[watching]} controls autoPlay className={`${frame} bg-black object-contain`} />
        : <img src={pictures[index] ?? pictures[0]} alt={product.name} className={`${frame} object-cover transition-transform duration-500 group-hover:scale-105`} />}
      {watching < 0 && <span className="absolute top-3 right-3 google-pill bg-white/90 backdrop-blur-xs text-google-teal font-semibold">{product.condition}</span>}
      {(pictures.length > 1 || videos.length > 0) && (
        <div className="absolute inset-x-0 bottom-0 flex items-center gap-1 bg-gradient-to-t from-black/60 to-transparent p-2">
          {watching >= 0 && <button type="button" onClick={() => setWatching(-1)} className="inline-flex items-center gap-1 rounded-full bg-white/90 px-2 py-0.5 text-xs font-semibold text-google-gray-800"><ImageIcon className="h-3 w-3" />Pictures</button>}
          {watching < 0 && pictures.length > 1 && pictures.map((src, i) => (
            <button key={src} type="button" aria-label={`Show picture ${i + 1} of ${pictures.length}`} aria-current={i === index} onClick={() => setIndex(i)}
              className={`h-1.5 rounded-full transition-all ${i === index ? 'w-5 bg-white' : 'w-1.5 bg-white/60'}`} />
          ))}
          {videos.map((src, i) => (
            <button key={src} type="button" onClick={() => setWatching(i)} className="ml-auto inline-flex items-center gap-1 rounded-full bg-white/90 px-2 py-0.5 text-xs font-semibold text-google-gray-800">
              <Play className="h-3 w-3" />{videos.length > 1 ? `Video ${i + 1}` : 'Watch video'}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

const BID = '/paas/bid/multi-seller/open/v1';
const ASSISTANT = '/paas/assistant/chat/text-to-text/v1';

export default function Storefront({ call, can, layout = 'grid', colour = '', onOpenBidding, onOpenAiAssistant }) {
  const [products, setProducts] = useState([]);
  const [busy, setBusy] = useState('');
  const [query, setQuery] = useState('');
  const [condition, setCondition] = useState('all');
  const [sort, setSort] = useState('featured');
  const [saved, setSaved] = useState({});      // product ids put on the wishlist from this screen
  const [passport, setPassport] = useState(null); // { name, data }
  const toast = useToast();

  useEffect(() => {
    getStorefront().then((data) => setProducts(data.products || [])).catch(() => setProducts([]));
  }, []);

  const conditions = ['all', ...Array.from(new Set(products.map((p) => p.condition).filter(Boolean)))];
  const shown = products
    .filter((p) => (condition === 'all' || p.condition === condition) && p.name.toLowerCase().includes(query.trim().toLowerCase()))
    .sort((a, b) => (sort === 'low' ? a.retail_price - b.retail_price : sort === 'high' ? b.retail_price - a.retail_price : sort === 'green' ? b.carbon_footprint_kg - a.carbon_footprint_kg : 0));

  const act = async (path, params, done) => {
    if (!can(path)) { toast('That feature is not available from this seller.'); return; }
    setBusy(path + params.product_id);
    try {
      const { name, ...sent } = params;
      const data = await call(path, sent);
      if (path === '/paas/passport/read/v1') setPassport({ name, data });
      else { toast(done); if (path === '/paas/wishlist/item/add/v1') setSaved((m) => ({ ...m, [params.product_id]: true })); }
    }
    catch (err) { toast(err.message || 'That did not work.'); }
    finally { setBusy(''); }
  };

  return (
    <Section title="Available products" subtitle={`${shown.length} of ${products.length} item${products.length === 1 ? '' : 's'} from this seller`}
      toolbar={products.length > 1 && (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <SearchBox value={query} onChange={setQuery} placeholder="Search products" />
            <Chips value={condition} onChange={setCondition} options={conditions.map((c) => ({ value: c, label: c === 'all' ? 'All' : c }))} />
          </div>
          <div className="w-48"><Dropdown ariaLabel="Sort products" value={sort} onChange={setSort} options={[{ value: 'featured', label: 'Featured' }, { value: 'low', label: 'Price: low to high' }, { value: 'high', label: 'Price: high to low' }, { value: 'green', label: 'Most CO2e saved' }]} /></div>
        </>
      )}>
      {products.length === 0 ? <Empty>No products to show yet.</Empty> : shown.length === 0 ? <Empty>No products match. Try a different search.</Empty> : (
        <div className={layout === 'list' ? 'grid grid-cols-1 gap-4' : 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5'}>
          {shown.map((product) => (
            <div key={product.id} className={`google-card lift group overflow-hidden flex ${layout === 'list' ? 'flex-row' : 'flex-col'}`}>
              <ProductMedia product={product} layout={layout} />
              <div className="p-4 flex flex-col flex-1">
                <h3 className="font-bold text-google-teal-dark text-base">{product.name}</h3>
                <div className="flex items-center gap-2 text-xs text-google-gray-600 mt-1 mb-3">
                  <span className="flex items-center gap-1 text-google-yellow font-bold"><Star className="h-3.5 w-3.5 fill-google-yellow" /> 4.8</span>
                  <span>•</span>
                  <span className="flex items-center gap-1 text-google-green font-medium"><Leaf className="h-3.5 w-3.5" /> {product.carbon_footprint_kg} kg CO2e saved</span>
                </div>
                <div className="flex items-baseline justify-between mb-3 pt-3 border-t border-google-gray-100">
                  <span className="text-sm line-through text-google-gray-400">${product.retail_price}</span>
                  {can(BID) && <div className="text-right">
                    <span className="text-xs text-google-teal font-semibold block">Bids from</span>
                    <span className="text-xl font-extrabold text-google-teal">${product.current_bidding_floor}</span>
                  </div>}
                </div>
                <div className="mt-auto space-y-2">
                  <div className="flex gap-2">
                    {can('/paas/order/cart/add/v1') && <button onClick={() => act('/paas/order/cart/add/v1', { product_id: product.id, quantity: 1 }, 'Added to your cart.')}
                      disabled={busy === '/paas/order/cart/add/v1' + product.id}
                      className="flex-1 google-btn-primary text-sm py-2 disabled:opacity-60">
                      <ShoppingCart className="h-4 w-4" /><span>Add to cart</span>
                    </button>}
                    {can('/paas/wishlist/item/add/v1') && <button onClick={() => act('/paas/wishlist/item/add/v1', { product_id: product.id }, 'Saved to your wishlist.')}
                      aria-label={saved[product.id] ? 'Saved to wishlist' : 'Save to wishlist'} className="google-btn-secondary !px-3 py-2">
                      <Heart className={`h-4 w-4 transition-all ${saved[product.id] ? 'fill-google-red text-google-red scale-110' : ''}`} />
                    </button>}
                  </div>
                  <div className="flex gap-2">
                    {can(BID) && <button onClick={() => onOpenBidding(product)} className="flex-1 google-btn-secondary text-sm py-2">
                      <Gavel className="h-4 w-4" /><span>Bid</span>
                    </button>}
                    {can('/paas/passport/read/v1') && <button onClick={() => act('/paas/passport/read/v1', { passport_id: product.passport_id, name: product.name }, '')}
                      aria-label="View passport" className="google-btn-secondary !px-3 py-2">
                      <QrCode className="h-4 w-4" />
                    </button>}
                    {can(ASSISTANT) && <button onClick={onOpenAiAssistant} aria-label="Ask the assistant" className="google-btn-secondary !px-3 py-2">
                      <Sparkles className="h-4 w-4" />
                    </button>}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {passport && (
        <Drawer title={`Passport: ${passport.name}`} onClose={() => setPassport(null)}>
          <ResultView data={passport.data} />
        </Drawer>
      )}
    </Section>
  );
}
