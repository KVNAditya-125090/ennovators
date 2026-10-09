import React from 'react';
import { BarChart3 } from 'lucide-react';

// Looker Studio report embed URL, e.g. https://lookerstudio.google.com/embed/reporting/<REPORT_ID>/page/<PAGE_ID>
// The report reads from the BigQuery dataset on the backend.
const LOOKER_URL = import.meta.env.VITE_LOOKER_STUDIO_URL;

export default function LookerStudioEmbed() {
  return (
    <div className="google-card p-5">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-bold text-google-teal-dark flex items-center space-x-2">
          <BarChart3 className="h-5 w-5 text-google-teal" />
          <span>Analytics</span>
        </h3>
        <span className="google-pill bg-google-blue-light text-google-blue-dark">Live data</span>
      </div>
      {LOOKER_URL ? (
        <iframe
          title="Analytics report"
          src={LOOKER_URL}
          className="w-full h-[480px] rounded-xl border border-google-gray-200"
          allowFullScreen
          sandbox="allow-storage-access-by-user-activation allow-scripts allow-same-origin allow-popups"
        />
      ) : (
        <div className="h-40 flex items-center justify-center rounded-xl border border-dashed border-google-gray-200 text-sm text-google-gray-600">
          The analytics dashboard has not been connected yet.
        </div>
      )}
    </div>
  );
}
