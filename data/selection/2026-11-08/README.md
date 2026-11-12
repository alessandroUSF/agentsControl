# Selection snapshot, 8 November 2026

The sources used to apply Amendment 1 of `docs/PREREGISTRATION.md`. Everything was downloaded on 8 November 2026 and is kept as downloaded.

- `aa_models_raw.json`: Artificial Analysis model records, extracted from artificialanalysis.ai/leaderboards/models. It uses Intelligence Index v5.0.1.
- `aa_open_sizes.json`: Artificial Analysis open-weights records with parameter counts, from the size pages.
- `or_market_share_month.json`: OpenRouter tokens by author per week (`/api/frontend/v1/rankings/market-share?view=month`).
- `or_models_month.json`: OpenRouter tokens by model per day (`/api/frontend/v1/rankings/models?view=month`).
- `or_v1_models.json`: the OpenRouter public model list (`/api/v1/models`). It is used to check API availability.
- `ollama_tags.json`: official Ollama library builds (tag, digest, size) for the candidate open models.
- `raw_pages/`: the original HTML pages, gzipped.
