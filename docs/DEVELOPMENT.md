# Resume development in VS Code

Open the **TechPulse repository folder**, not the installed app folder. Read PROJECT_HANDOFF.md and AGENTS.md first. Python/debugpy/Pylance extensions are recommended in .vscode/extensions.json; they were already installed on the development host.

## Environment

```powershell
uv sync --frozen --extra dev
```

The project's .venv is ignored by Git. Debug configurations explicitly use .venv/Scripts/python.exe. If uv is unavailable, install uv using its official instructions before synchronizing; do not copy an existing venv from another directory.

## Run and verify

- **F5**: choose TechPulse: Desktop (isolated development data). Uses source from this workspace and private state under user-data/development, separate from the installed app's personal database.
- **Run and Debug**: TechPulse: Native smoke check opens all16 pages in both workspaces and exits; uses user-data/smoke.
- **Terminal > Run Task**: TechPulse: Tests, TechPulse: Lint, or TechPulse: Type check. The test task selects offscreen Qt; use native Windows smoke/visual review for GUI changes.
- Python Testing panel uses pytest with tests/ as its root.

Optional SEC/provider configuration can be set in the environment or an untracked .env file. Never commit credentials/contact details or invent a SEC_USER_AGENT. No SEC live verification is implied by fixture tests. The current feature backlog/acceptance criteria are in TASKS.md and PROJECT_HANDOFF.md.

## Refresh the desktop installation

Close installed TechPulse windows safely, then run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\packaging\install_windows.ps1 -NoLaunch
```

The installed copy has its own runtime/source under LOCALAPPDATA/Programs/TechPulse. Verify hashes/tests after changes, preserve LOCALAPPDATA/TechPulse personal data, and update/archive PROJECT_HANDOFF.md after every development pass. Do not force-close user sessions. Public release assets remain separate from current main.
