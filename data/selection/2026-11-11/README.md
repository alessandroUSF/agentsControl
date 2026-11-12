# OpenRouter endpoints snapshot, 11 November 2026

Downloaded on 11 November 2026 at 08:09 UTC (03:09 EST), with public requests that need no account and no key. Everything is kept as downloaded. No model was called.

- `raw/or_endpoints_<author>_<slug>.json`: the endpoints (serving hosts) of each model reached through OpenRouter: models 7, 8, 10, 12, 13, 14 and 22, and the candidate model 23 (`thedrummer/cydonia-24b-v4.1`). Source: `/api/v1/models/<author>/<slug>/endpoints`.
- `raw/or_endpoints_zdr.json`: OpenRouter's list of zero-data-retention endpoints (`/api/v1/endpoints/zdr`).
- `raw/or_v1_models.json`: OpenRouter's public model list (`/api/v1/models`).

Used for the host fixed for each model reached through OpenRouter (decision D16) and for the zero-retention check of model 23 (decision D15), both recorded in `docs/PI_DECISIONS.md` on 11 November 2026. The selection snapshot of 8 November is in `../2026-11-08/`.
