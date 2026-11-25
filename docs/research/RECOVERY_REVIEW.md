# Targeted recovery safety review

Date2026-11-25. A separate provider/security reviewer inspected recovery.py, startup schema handling and tests read-only. Baseline11 recovery cases passed; small synthetic probes identified four defects, all corrected and independently rechecked:

- A deadline exception in SQLite's final SQLITE_DONE callback can happen after commit. The callback now skips deadline/cap exceptions at DONE; postcommit cleanup failure returns success with a warning. An independently injected cleanup failure retained the safety copy and reported the committed restore accurately.
- Store startup previously accepted an unrelated database with user_version1 and added project tables. Canonical schema validation now runs before WAL/schema initialization; a regression confirms unrelated data is unchanged.
- Column names alone did not establish keys/types/constraints. Canonical SQL and full table_info are compared with the app's own schema, and unexpected triggers/views/custom indexes are rejected.
- A small main file can hide a larger WAL-backed logical database. Logical page_count×page_size limits now run before/during copy and validation; a small synthetic WAL probe/regression exercises this.

Reviewer reran19 recovery tests successfully and found no further actionable issue within that scope. Lead additionally tested Settings cancel/apply/corruption flows, nonfinite/logically invalid payloads, transaction rollback and schema/row/field limits. No actual private database was restored during development.

Concurrency limit: close other TechPulse sessions. Writes made after the pre-restore snapshot by another process are not guaranteed in that safety copy. The feature does not introduce cross-process coordination or automatic schema migration. Current unsupported/corrupt startup recovery remains manual.

Primary implementation references: [Python sqlite3 backup](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup), [SQLite backup API](https://www.sqlite.org/backup.html). Reviewed2026-11-25. Tests/probes establish the covered behavior, not a certification against every storage failure or malicious SQLite file.
