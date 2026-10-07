# Looker Studio

Dashboards for the Owner console. No application code lives here: the report is built in Looker Studio
with the BigQuery dataset (see `../bigquery/`) as its data source.

The report is embedded by `../firebase_hosting/src/users/owner/LookerStudioEmbed.jsx`.
Set `VITE_LOOKER_STUDIO_URL` (the report's embed URL) in `firebase_hosting/.env.local`.
