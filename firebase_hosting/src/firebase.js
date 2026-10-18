import { initializeApp } from 'firebase/app'
import { getAnalytics, isSupported } from 'firebase/analytics'

// Web app config. These values identify the project and are safe to ship in the client bundle.
const firebaseConfig = {
  apiKey: 'AIzaSyCdxYtPZRX2K41N0sLkS1OeNLr2NMov58c',
  authDomain: 'lakshmi-dbc6b.firebaseapp.com',
  projectId: 'lakshmi-dbc6b',
  storageBucket: 'lakshmi-dbc6b.firebasestorage.app',
  messagingSenderId: '378519086992',
  appId: '1:378519086992:web:e39b995f21f3d47dd4b515',
  measurementId: 'G-D1PQLFTD78',
}

export const app = initializeApp(firebaseConfig)

// Analytics only works in supported browsers (not with blocked cookies or in non-browser contexts).
export const analyticsReady = isSupported().then((ok) => (ok ? getAnalytics(app) : null))
