import React, { useRef, useState } from 'react';
import { ImagePlus, X, Film, Loader2 } from 'lucide-react';
import { loadSession } from '../../services/maas/session';

// Photos and videos for a product, uploaded as the person picks them. The same limits are enforced by the server
// (cloud_run/media.py), which also reads the real type of each file; these checks only save a wasted upload.
const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
const VIDEO_TYPES = ['video/mp4', 'video/webm'];
const MAX_IMAGE = 10 * 1024 * 1024;
const MAX_VIDEO = 100 * 1024 * 1024;
const MAX_FILES = 10;

const mb = (n) => `${(n / (1024 * 1024)).toFixed(n > 10 * 1024 * 1024 ? 0 : 1)} MB`;

// Sends one file as the request body; reports progress; resolves to { url, kind }
function send(tenantId, file, onProgress) {
  return new Promise((resolve, reject) => {
    const email = loadSession()?.email;
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `/api/v1/consumer/media?filename=${encodeURIComponent(file.name)}`);
    xhr.setRequestHeader('X-Tenant-Id', tenantId || '');
    if (email) xhr.setRequestHeader('X-User-Email', encodeURIComponent(email));
    xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
    xhr.upload.onprogress = (e) => { if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100)); };
    xhr.onerror = () => reject(new Error('The upload could not reach the platform. Check that it is running.'));
    xhr.onload = () => {
      let body = null;
      try { body = JSON.parse(xhr.responseText); } catch { /* not JSON */ }
      if (xhr.status >= 200 && xhr.status < 300 && body?.url) resolve({ url: body.url, kind: body.kind });
      else reject(new Error(body?.detail?.message || `The upload failed (${xhr.status}).`));
    };
    xhr.send(file);
  });
}

// value: [{ url, kind: 'image' | 'video' }]. onChange gets the new list. onBusy(true/false) says whether an upload is running.
export default function MediaField({ tenantId, value, onChange, onBusy, label = 'Photos and videos' }) {
  const input = useRef(null);
  const [pending, setPending] = useState([]); // [{ id, name, progress, error }]
  const done = useRef(value);
  done.current = value;

  const setBusy = (list) => { setPending(list); onBusy?.(list.some((p) => !p.error)); };

  const pick = async (fileList) => {
    const files = [...fileList];
    if (input.current) input.current.value = '';
    let room = MAX_FILES - done.current.length;
    const queue = [];
    const rejected = [];
    for (const file of files) {
      const isImage = IMAGE_TYPES.includes(file.type);
      const isVideo = VIDEO_TYPES.includes(file.type);
      if (!isImage && !isVideo) rejected.push({ id: `${file.name}-${Math.random()}`, name: file.name, error: 'Use JPG, PNG, WebP or GIF pictures, or MP4 or WebM videos.' });
      else if (file.size > (isImage ? MAX_IMAGE : MAX_VIDEO)) rejected.push({ id: `${file.name}-${Math.random()}`, name: file.name, error: `Too large (${mb(file.size)}). Pictures up to 10 MB, videos up to 100 MB.` });
      else if (room <= 0) rejected.push({ id: `${file.name}-${Math.random()}`, name: file.name, error: `A product can have up to ${MAX_FILES} files.` });
      else { room -= 1; queue.push({ id: `${file.name}-${Math.random()}`, name: file.name, progress: 0, file }); }
    }
    let list = [...rejected, ...queue.map(({ file, ...rest }) => rest)];
    setBusy(list);
    for (const item of queue) {
      try {
        const saved = await send(tenantId, item.file, (progress) => { list = list.map((p) => (p.id === item.id ? { ...p, progress } : p)); setBusy(list); });
        done.current = [...done.current, saved];
        onChange(done.current);
        list = list.filter((p) => p.id !== item.id);
      } catch (err) {
        list = list.map((p) => (p.id === item.id ? { ...p, error: err.message } : p));
      }
      setBusy(list);
    }
  };

  const remove = (url) => onChange(value.filter((m) => m.url !== url));

  return (
    <div>
      <span className="block mb-1 text-base font-semibold text-google-gray-800">{label}<span className="font-normal text-google-gray-500"> (optional)</span></span>
      <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
        {value.map((m, i) => (
          <div key={m.url} className="relative aspect-square overflow-hidden rounded-lg border border-google-gray-200 bg-google-gray-50">
            {m.kind === 'video'
              ? <video src={m.url} muted preload="metadata" className="h-full w-full object-cover" aria-label={`Video ${i + 1}`} />
              : <img src={m.url} alt={`Picture ${i + 1}`} className="h-full w-full object-cover" />}
            {m.kind === 'video' && <span className="absolute bottom-1 left-1 inline-flex items-center gap-1 rounded bg-black/60 px-1.5 py-0.5 text-xs text-white"><Film className="h-3 w-3" />Video</span>}
            {i === 0 && m.kind === 'image' && <span className="absolute left-1 top-1 rounded bg-white/90 px-1.5 py-0.5 text-xs font-semibold text-google-teal">Cover</span>}
            <button type="button" aria-label={`Remove ${m.kind} ${i + 1}`} onClick={() => remove(m.url)} className="absolute right-1 top-1 rounded-full bg-white/90 p-1 text-google-gray-700 shadow hover:bg-white"><X className="h-3.5 w-3.5" /></button>
          </div>
        ))}
        {value.length < MAX_FILES && (
          <button type="button" onClick={() => input.current?.click()} className="flex aspect-square flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed border-google-gray-300 text-sm text-google-gray-600 hover:border-google-teal hover:text-google-teal">
            <ImagePlus className="h-5 w-5" />Add files
          </button>
        )}
      </div>
      <input ref={input} type="file" multiple accept={[...IMAGE_TYPES, ...VIDEO_TYPES].join(',')} className="sr-only" aria-label="Choose photos and videos" tabIndex={-1} onChange={(e) => pick(e.target.files)} />
      {pending.length > 0 && (
        <ul className="mt-2 space-y-1" aria-live="polite">
          {pending.map((p) => (
            <li key={p.id} className={`flex items-center gap-2 text-sm ${p.error ? 'text-google-red' : 'text-google-gray-600'}`}>
              {p.error ? <X className="h-4 w-4 shrink-0" /> : <Loader2 className="h-4 w-4 shrink-0 animate-spin" />}
              <span className="min-w-0 truncate">{p.name}</span>
              <span className="shrink-0">{p.error ? p.error : `${p.progress}%`}</span>
              {p.error && <button type="button" onClick={() => setBusy(pending.filter((x) => x.id !== p.id))} className="ml-auto shrink-0 underline">Dismiss</button>}
            </li>
          ))}
        </ul>
      )}
      <span className="mt-1 block text-sm text-google-gray-500">JPG, PNG, WebP or GIF up to 10 MB each. MP4 or WebM video up to 100 MB. The first picture is the cover. Up to {MAX_FILES} files.</span>
    </div>
  );
}
