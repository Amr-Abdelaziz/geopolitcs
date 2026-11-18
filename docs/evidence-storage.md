# Evidence storage

Collected evidence and documents submitted to `POST /api/evidence` are stored in
the application's SQLite database. `GET /api/evidence` reloads persisted evidence,
including after a server restart. The new tables are created automatically without
changing existing assessment or radar records.

- Feed and web-search IDs use a SHA-256 digest of the canonical URL, with provider
  IDs or source/title as the fallback when no URL exists. Identity is stable within
  each ingestion provider; cross-provider syndicated-story clustering is not included.
- URL fragments and common tracking parameters are removed. Identity parameters
  such as article IDs remain intact.
- Each evidence record has a content hash. Changed content is retained in
  `evidence_versions`; `evidence` contains the latest ingested version. Existing
  assessment citations remain snapshots of the evidence used for that assessment.
- The first ingestion timestamp is preserved. Publication dates come from the
  source, and missing or invalid dates remain null. Knowledge documents have an
  optional `published_at` field separate from their local `created_at` timestamp.
- `DEMO_EVIDENCE=0` is the default. Set it to `1` explicitly to include fixture
  evidence, labeled `DEMO /`, marked `is_demo`, and rated unknown. These fixtures
  are never persisted. `MOCK_LLM` does not enable fixture evidence.
- Collection no longer fills sparse country matches with unrelated documents.
- Citation validation accepts numeric, feed, web, and knowledge-base evidence IDs.
  It checks that references exist; it does not yet verify that a passage supports
  the associated claim.

This migration does not revalidate historical assessments or the curated knowledge
documents' existing reliability ratings. Full-document ingestion, ranked retrieval,
source corroboration, and passage-level claim verification remain separate work.

Regression checks:

```powershell
New-Item -ItemType Directory -Force logs | Out-Null
.venv/Scripts/python.exe -m pytest tests/test_evidence_storage.py tests/test_verification.py tests/test_database_and_radar.py tests/test_pipeline.py tests/test_api.py tests/test_knowledge_base.py tests/test_web_search.py -q -p no:cacheprovider --basetemp=logs/pytest-evidence
```
