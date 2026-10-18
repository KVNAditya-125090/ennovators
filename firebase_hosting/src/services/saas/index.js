// SaaS - Support as a Service
import { request, postJson } from '../http';

// Grades a returned item from a photo (a data URL from shrinkPhoto); needs sign-in
export const triageReturn = (itemId, imageBase64, itemName = '') =>
  postJson('/api/v1/saas/returns/triage', { item_id: itemId, image_base64: imageBase64, item_name: itemName });
export const getTickets = () => request('/api/v1/saas/tickets');
