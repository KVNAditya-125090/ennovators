// The demo accounts: every email and password is made up, and they are shown on the sign-in screen under "Try a demo account".
// `key` is what /demo-login/<key> signs in as, so a person (or a test) can open a portal without typing anything.
export const DEMO_ACCOUNTS = [
  { key: 'manager', group: 'Owner', role: 'Manager', email: 'manager.owner@aionos.ai', password: 'Manager@Demo2026' },
  { key: 'developer', group: 'Owner', role: 'Developer', email: 'developer.owner@aionos.ai', password: 'Developer@Demo2026' },
  { key: 'operator', group: 'Owner', role: 'Operator', email: 'operator.owner@aionos.ai', password: 'Operator@Demo2026' },
  { key: 'root', group: 'Consumer', role: 'Root', email: 'it.consumer@lakshmi.com', password: 'IT@Lakshmi2026' },
  { key: 'marketing', group: 'Consumer', role: 'Marketing', email: 'marketing.consumer@lakshmi.com', password: 'Marketing@Lakshmi2026' },
  { key: 'operation', group: 'Consumer', role: 'Operation', email: 'operation.consumer@lakshmi.com', password: 'Operation@Lakshmi2026' },
  { key: 'support', group: 'Consumer', role: 'Support', email: 'support.consumer@lakshmi.com', password: 'Support@Lakshmi2026' },
  { key: 'customer', group: 'Customer', role: 'Individual', email: 'individual.customer@gmail.com', password: 'Customer@Lakshmi2026' }
];
