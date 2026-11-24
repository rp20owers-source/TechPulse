# Independent release readiness review

Reviewer: Codex product/release subagent. Date: 2026-11-24. App checkpoint inspected: `ccdc750` on main, with contemporaneous working-tree packaging changes owned by the lead. This review does not certify a completed installer, public binary release or legal compliance. It records observed evidence and concrete remaining gates.

## Distribution decision

**Source-only research preview is the appropriate initial public release scope.** Publish the application's own source, lockfile, documentation, tests and explicitly fictional example assets after the lead's repository/security checks. Do not attach a public Windows executable merely because PyInstaller produces one. The local portable build is an engineering preview for further validation; its redistributable dependency set and clean-machine behavior remain separate acceptance gates.

No actual market-data cache, imported financial disclosures, personal database, credentials, generated private report or live-provider fixture belongs in a repository or release. The inspected screenshots contain SYN fictional assets and a prominent demonstration banner.

## Observed Qt environment and license evidence

The shared development environment reports:

| Distribution | Installed version | Observed metadata |
|---|---|---|
| PySide6 | 6.12.0 | `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only` |
| PySide6_Essentials | 6.12.0 | Same license expression |
| PySide6_Addons | 6.12.0 | Same license expression |
| shiboken6 | 6.12.0 | Same license expression |
| Qt runtime (`qVersion()`) | 6.12.0 | Runtime version queried directly |

Inventory method: Python `importlib.metadata.distribution()` version/license/files; inspect matching dist-info licenses and search installed PySide6/shiboken6 file paths for license/copying/notice/SBOM names. Each inspected dist-info listed only `LicenseRef-Qt-Commercial.txt`; its text concerns holders of valid commercial Qt licenses. No LGPL/GPL text or third-party notice inventory was found by that installed-file-name search. This does **not** change the metadata's offered open-source paths; it means copying those wheel license directories alone is not evidence of a complete binary-notices package. The lead owns the full final artifact inventory and notice collection.

Qt's official guidance requires LGPL notices/license text, corresponding library source or an appropriate source offer, and practical replacement/relinking rights; it also distinguishes GPL-only modules and third-party terms. Dynamic linking alone does not complete those obligations. See [official LGPL obligations](https://www.qt.io/development/open-source-lgpl-obligations) and [Qt for Python license overview](https://doc.qt.io/qtforpython-6/licenses.html), accessed 2026-11-24.

## Corresponding-source availability checked

Official directory listings were opened successfully on 2026-11-24:

- [PySide6 6.12.0 source directory](https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.12.0-src/) lists `pyside-setup-everywhere-src-6.12.0.zip` and `.tar.xz`.
- [Qt 6.12.0 combined source directory](https://download.qt.io/official_releases/qt/6.12/6.12.0/single/) lists `qt-everywhere-src-6.12.0.zip` and `.tar.xz`.
- [Qt 6.12.0 module source directory](https://download.qt.io/official_releases/qt/6.12/6.12.0/submodules/) lists module-specific archives.

These are **verified upstream listings**, not downloaded, hashed, extracted or rebuilt corresponding-source packages. A bare upstream URL is not this project's completed compliance mechanism. Before public binary conveyance, map every bundled Qt/PySide/shiboken library, plugin and third-party component to the exact build's source, patches, notices and build/replacement information, then implement the chosen delivery/offer mechanism. Retain evidence and verify its continued accessibility. Do not claim the installed wheel's binary build is reproduced merely from a matching version string.

The [official Qt 6.12 release index](https://download.qt.io/official_releases/qt/6.12/) also lists 6.12.1 and security-patch files as of the review date. Patch applicability to the exact locked wheels and included modules has not been established. Triage those advisories against the final artifact; their listing is not evidence that every listed issue is reachable in this app.

## Public Windows binary acceptance gates

| Gate | Evidence required before public binary publication | Review status |
|---|---|---|
| Exact artifact identity | Build commit, lockfile, OS/Python/tool versions, artifact hashes, dependency/module manifest and reproducible command | Lead building; final manifest not independently inspected |
| Dependency notices | Exact packaged components and license texts/notices, including Python/runtime, Qt plugins and native transitive libraries | Incomplete in installed-wheel inventory; lead collecting |
| Qt source/replacement | Exact-source delivery or compliant offer, patches/build instructions, documented and tested user library replacement/relinking route, preserved recipient rights | Open |
| Module license scope | Inspect actual collected Qt modules/plugins; exclude unintended GPL-only or unused components, or explicitly satisfy their applicable terms | Open until final package inventory |
| Dependency security | Scan/review exact locked and bundled versions; triage official advisories and document residual findings | Final artifact triage open |
| Clean-machine execution | Windows VM without Python/Qt/dev tools: extract/install, offline launch, all workspaces, import/export, local paths, permissions and ordinary-user execution | Not executed by this reviewer |
| Data lifecycle | Upgrade/back up/restore/recovery, portable vs installed state, locked files, interrupted writes and safe uninstall preserving user research | Partially covered by unit checks; clean-machine scenarios open |
| Packaging UX | Installer or clearly documented portable operation, shortcuts/icons, version identification, failure logs and release notes | Portable preview under lead development; professional installer open |
| Provenance and integrity | Public release corresponds to tested source/build, checksum verification and a documented unsigned/signed status | Public binary gate open; never imply signature without verification |
| Product accuracy | Preview wording and requirement matrix preserve unimplemented discovery/forecast/data-coverage limits | Product review supports preview scope; final matrix owned by lead |

Signing can be a later trust improvement when an appropriate certificate is available; it must never be fabricated or described as a prerequisite imposed by this review for all local engineering use. Public binary publication still requires the source/license and artifact-validation gates above.

## GUI regression evidence for this checkpoint

The generic table now clears the initial sort indicator before enabling sorting. A native Windows Qt test preserved supplied `B/A/C` order; two actual numeric header clicks sorted values `2/10/30` and reversed the order. The technology movers page displayed SYN-AI first, matching its highest supplied five-period return. This resolves the independent product review's initial-ranking defect without removing manual sorting.

Fresh dark dashboard and movers captures were generated from an isolated SQLite store using the Windows backend. The window was 1480×940 logical units at the host's 1.25 device ratio, producing 1850×1175 image pixels. The reviewer inspected both images; text, demonstration banner, table ranking and layout were readable. Captures and temporary state were saved under `work/review-final`, not committed as private state or a runtime dataset. The lead may copy the approved fictional screenshots into user deliverables.

## Scope still unverified

This reviewer did not build or execute the final PyInstaller artifact, install on a clean VM, audit every transitive native license, download/reproduce Qt source builds, run a full vulnerability scanner, exercise live Alpaca/CoinGecko feeds, or validate an investment strategy. The earlier native page checks and corrected sort behavior support usability of a preview, not a production-release or financial-performance claim.
