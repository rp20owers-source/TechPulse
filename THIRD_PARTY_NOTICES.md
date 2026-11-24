# Third-party software and data boundaries

TechPulse's original code is MIT. It does not relicense dependencies, market data, political records, government-linked third-party documents or provider API rights. No proprietary datasets are bundled. Exact package versions/hashes are in uv.lock and requirements.lock.

## Runtime libraries

| Component | License family / distribution decision |
|---|---|
| Python/stdlib | PSF license and included third-party notices |
| PySide6, Shiboken6, Qt | LGPLv3 / alternate GPL or commercial terms depending on module; source use selects appropriate open-source terms. No GPL-only Qt module is intentionally used. Only Core/Gui/Widgets are imported directly. PyQtGraph may dynamically use other Qt modules; packaged inventory requires inspection. |
| PyQtGraph | MIT; color-map files may include CC BY notices. Do not strip included notices. |
| NumPy | BSD family plus multiple bundled third-party licenses (OpenBLAS/LAPACK/etc as applicable to wheel). Preserve wheel license inventory. |
| HTTPX/httpcore/h11 | BSD/MIT families; retain exact locked distribution notices |
| anyio/idna/typing extensions/certifi | Individual MIT/BSD/PSF/MPL terms; certifi's Mozilla CA bundle includes MPL conditions |
| ReportLab/Pillow | BSD-style/HPND and bundled font/image-component notices; do not relicense font files |

The dependency installation process fetches the upstream packages for the user. The **public preview release ships source, not a prebundled Qt binary**. Runtime license files remain in installed distributions. The packaged-executable build creates an auditable local development artifact, not an automatically approved public release.

## Qt binary release gate

Read [Qt LGPL obligations](https://www.qt.io/development/open-source-lgpl-obligations) and [Qt for Python licenses](https://doc.qt.io/qtforpython-6/licenses.html). A dynamic DLL build alone does not complete compliance. Before public executable publication:

1. Inventory exact binaries/modules/patch versions and all third-party licenses; exclude unused GPL-only modules and development tools.
2. Ship LGPL/GPL and required notices, plus corresponding Qt/PySide/Shiboken source or a compliant maintained source offer. Verify exact versions and source availability, not merely a moving latest link.
3. Provide build information and practical DLL replacement/relinking instructions. Permit reverse engineering needed to debug modified libraries; no EULA restriction may override those rights.
4. Keep modified libraries and patches available under their required terms. TechPulse currently makes no Qt library patches.
5. Triage upstream security updates, test a clean Windows machine and test source/DLL replacement before signing and public binary upload.

Source directories inspected during research are documented in docs/research/RELEASE_READINESS.md. The installed wheels were observed to contain incomplete open-source license text in dist-info; do not assume wheel metadata is a sufficient notice bundle. The local builder includes available distribution license files and GNU text, but that is only part of the gate.

No OpenBB, proprietary competitor strategies, chart scripts or logos are copied. Competitor research is linked under docs/research/COMPETITIVE_ANALYSIS.md. Underlying data permissions remain independent of software licensing.
