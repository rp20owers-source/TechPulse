# Security policy

This is an early research preview. Please report a vulnerability through [GitHub private vulnerability reporting](https://github.com/rp20owers-source/TechPulse/security/advisories/new) when available. If unavailable, open an issue asking for a private channel without including secrets, exploit details or personal data. No response SLA is promised.

No telemetry, trade execution or runtime LLM exists. Credentials are read from environment variables, never saved by TechPulse. Provider diagnostics do not disclose headers or raw bodies. Network requests are manual, read-only, HTTPS, no redirects, bounded response size and cooperative operation budget. Provider snapshots remain in session memory; no raw data is shipped in the repository.

SQLite, archives and backups are **unencrypted**. Import only data whose terms permit this storage. Protect the OS account and backups. A source URL must be public and free of credentials; common secret query/fragment names are rejected, but automatic detection cannot recognize every possible secret encoding. Do not place secrets in source names, URLs, notes or CSVs.

Imports are bounded to20MB/100,000 rows and128KiB per CSV field, validated before transaction commit. This bounds inputs but does not guarantee fast rendering of a100,000-row Qt table. HTML escapes user values, external report links are not automatically opened, and CSV scalar cells are protected from formula prefixes. Database schema version1 is currently the only supported version.

Security review and synthetic tests are documented, not a penetration-test certification. Dependency vulnerability scanning, signed installers, encrypted provider caches and clean-machine release testing remain gates. Provider legal/use restrictions remain independent of software security.

SEC contact can optionally be entered in Settings for the current session; it is sent only as the declared SEC request header, never saved by the app. Header control/non-ASCII characters and values over256 characters are rejected with redacted errors. Clearing restores any existing environment fallback and does not cancel an already active request.
