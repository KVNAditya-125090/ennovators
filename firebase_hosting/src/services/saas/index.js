// SaaS - Support as a Service
import { request, postJson } from '../http';

export const triageReturn = (itemId, imageUrl) =>
  postJson('/api/v1/saas/returns/triage', { item_id: itemId, image_url: imageUrl });
export const getTickets = () => request('/api/v1/saas/tickets');
