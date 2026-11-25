"""Native Qt research terminal. Network access is explicit and runs off the GUI thread."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pyqtgraph as pg
from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .analytics import contract_metrics, detect_patterns, indicators, option_metrics, walk_forward
from .demo import seed_demo
from .reports import SECTIONS, export_report, html_text, snapshot
from .research import asset_rows, correlations, disclosure_performance, opportunity
from .store import Store, data_directory, utc_now
from .tables import ResearchTable

PAGES = [
    "Dashboard",
    "Technology Movers",
    "Emerging Technology",
    "Cryptocurrency",
    "Unusual Options Activity",
    "Chart Analysis & Forecasts",
    "Government Contracts",
    "Nancy Pelosi Tracker",
    "Donald Trump Tracker",
    "Investment Opportunities",
    "Watchlists",
    "Paper Portfolio",
    "Weekly Reports",
    "Report Archive",
    "Data Sources & Health",
    "Settings",
]
SUBTITLES = {
    "Dashboard": "Your research workspace. Follow the evidence, understand the uncertainty.",
    "Technology Movers": "Explore your technology universe across 1, 5 and 21 observations.",
    "Cryptocurrency": "An independent view of digital assets, liquidity and cross-market relationships.",
    "Investment Opportunities": "Connect independent signals. Missing evidence is a reason to abstain.",
    "Data Sources & Health": "Know where each observation comes from, and what it cannot tell you.",
}


def fmt(value, digits=2):
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (float, int)):
        if abs(value) >= 1e12:
            return f"{value / 1e12:,.2f}T"
        if abs(value) >= 1e9:
            return f"{value / 1e9:,.2f}B"
        if abs(value) >= 1e6:
            return f"{value / 1e6:,.2f}M"
        if 0 < abs(value) < 0.01:
            return f"{value:.6f}"
        return f"{value:,.{digits}f}"
    return str(value)


def label(text, name=None, wrap=True):
    obj = QLabel(str(text))
    obj.setWordWrap(wrap)
    obj.setTextFormat(Qt.TextFormat.PlainText)
    if name:
        obj.setObjectName(name)
    return obj


def button(text, callback, primary=False):
    obj = QPushButton(text)
    obj.setCursor(Qt.CursorShape.PointingHandCursor)
    obj.clicked.connect(callback)
    if primary:
        obj.setObjectName("primary")
    return obj


def card(title=None):
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 17, 20, 17)
    layout.setSpacing(12)
    if title:
        layout.addWidget(label(title, "cardTitle"))
    return frame, layout


def table(rows, columns, min_height=280):
    return ResearchTable(rows, columns, fmt, min_height)


class WorkerSignals(QObject):
    success = Signal(object)
    failed = Signal(str)


class Worker(QRunnable):
    def __init__(self, fn):
        super().__init__()
        self.fn = fn
        self.signals = WorkerSignals()

    def run(self):
        try:
            self.signals.success.emit(self.fn())
        except Exception as exc:
            # ProviderError messages are redacted inside provider layer.
            from .providers import ProviderError

            self.signals.failed.emit(
                str(exc)
                if isinstance(exc, (ProviderError, ValueError))
                else "Request failed. Check network access and provider configuration."
            )


class MainWindow(QMainWindow):
    def __init__(self, store=None):
        super().__init__()
        self.store = store or Store()
        seed_demo(self.store)
        self.closed = False
        self.recovery_busy = False
        self.last_recovery_point = ""
        self.mode = "demo"
        self.page = "Dashboard"
        self.active_symbol = "SYN-AI"
        self.theme = self.store.setting("theme", "dark")
        self.live_results = []
        self.sec_user_agent = ""  # Explicit session-only contact, never persisted.
        self.worker: Worker | None = None
        self.page_errors: list[str] = []
        self.setWindowTitle("TechPulse · Financial research terminal")
        self.setWindowIcon(QIcon(str(Path(__file__).parent / "assets" / "techpulse.svg")))
        self.resize(1480, 940)
        self.setMinimumSize(1100, 720)
        root = QWidget()
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setSpacing(0)
        shell.setContentsMargins(0, 0, 0, 0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(245)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 25, 16, 16)
        side.addWidget(label("◉  TechPulse", "brand"))
        side.addWidget(label("FINANCIAL INTELLIGENCE", "eyebrow"))
        side.addSpacing(24)
        side.addWidget(label("RESEARCH WORKSPACE", "eyebrow"))
        self.nav = QListWidget()
        self.nav.setObjectName("navigation")
        self.nav.setSpacing(2)
        for name in PAGES:
            item = QListWidgetItem(name)
            item.setToolTip(name)
            self.nav.addItem(item)
        self.nav.setCurrentRow(0)
        self.nav.currentTextChanged.connect(self.navigate)
        side.addWidget(self.nav, 1)
        side.addWidget(label("LOCAL FIRST  /  v0.1 preview", "eyebrow"))
        side.addWidget(label("Independent research.\nNo trade execution.", "muted"))
        shell.addWidget(sidebar)
        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(30, 24, 30, 18)
        main_layout.setSpacing(16)
        top = QHBoxLayout()
        top.addWidget(label("RESEARCH TERMINAL", "eyebrow"))
        top.addStretch()
        self.workspace = QComboBox()
        self.workspace.setAccessibleName("Data workspace")
        self.workspace.addItems(["Fictional demo", "Personal research"])
        self.workspace.currentIndexChanged.connect(self.change_workspace)
        top.addWidget(self.workspace)
        top.addWidget(button("Import CSV", self.import_dialog, True))
        main_layout.addLayout(top)
        self.title = label("Dashboard", "pageTitle")
        self.subtitle = label(SUBTITLES["Dashboard"], "muted")
        main_layout.addWidget(self.title)
        main_layout.addWidget(self.subtitle)
        self.banner = label("", "banner")
        main_layout.addWidget(self.banner)
        self.body_scroll = QScrollArea()
        self.body_scroll.setWidgetResizable(True)
        self.body_scroll.setFrameShape(QFrame.Shape.NoFrame)
        main_layout.addWidget(self.body_scroll, 1)
        self.status = label("Ready · local SQLite · no network activity", "muted")
        main_layout.addWidget(self.status)
        shell.addWidget(main, 1)
        self.apply_theme()
        self.rebuild_page()
        self.scheduler = QTimer(self)
        self.scheduler.timeout.connect(self.check_schedule)
        self.scheduler.start(60_000)
        QTimer.singleShot(2000, self.check_schedule)

    def apply_theme(self):
        dark = self.theme == "dark"
        instance = QApplication.instance()
        if instance is not None:
            instance.setProperty("techpulse_theme", self.theme)
        bg, panel, side, text, muted, border, alternate = (
            ("#0b1220", "#111d2f", "#0e1726", "#e8eef7", "#91a2b9", "#223248", "#142135")
            if dark
            else ("#f1f4f9", "#ffffff", "#e7edf6", "#13243b", "#5c6f89", "#d5dfea", "#f5f8fc")
        )
        self.colors = {"bg": bg, "panel": panel, "text": text, "muted": muted, "border": border}
        self.setStyleSheet(f"""
        QWidget {{ background:{bg}; color:{text}; font-family:'Segoe UI'; font-size:13px; }}
        QFrame#sidebar {{background:{side}; border-right:1px solid {border};}}
        QFrame#sidebar QLabel {{background:transparent;}}
        QLabel#brand {{font-size:27px;font-weight:700;letter-spacing:-1px;color:{text};}}
        QLabel#eyebrow {{font-size:10px;font-weight:600;letter-spacing:1.4px;color:{muted};}}
        QLabel#pageTitle {{font-size:29px;font-weight:650;letter-spacing:-.6px;}}
        QLabel#muted {{color:{muted};font-size:12px;}}
        QLabel#banner {{background:{"#24261f" if dark else "#fff5dc"};color:{"#e3c47c" if dark else "#78570e"};border:1px solid {"#4c452d" if dark else "#e5ce97"};border-radius:7px;padding:11px;font-size:12px;}}
        QFrame#card {{background:{panel};border:1px solid {border};border-radius:10px;}}
        QFrame#card QLabel {{background:transparent;}}
        QLabel#cardTitle {{font-size:15px;font-weight:600;}}
        QLabel#metric {{font-size:29px;font-weight:600;}}
        QLabel#accent {{color:{"#37c5b1" if dark else "#116f61"};font-size:12px;}}
        QListWidget#navigation {{background:transparent;border:0;outline:0;font-size:12px;}}
        QListWidget#navigation::item {{padding:8px 9px;border-radius:6px;}}
        QListWidget#navigation::item:selected {{background:{"#163c40" if dark else "#d2ebe7"};color:{"#66dfca" if dark else "#086d64"};font-weight:600;}}
        QListWidget#navigation::item:hover {{background:{alternate};}}
        QPushButton {{background:{panel};border:1px solid {border};border-radius:6px;padding:8px 13px;font-weight:500;}}
        QPushButton:hover {{border-color:#38bba8;}}
        QPushButton:disabled {{color:{muted};}}
        QPushButton#primary {{background:#24b7a4;color:#042e2a;border-color:#24b7a4;font-weight:650;}}
        QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox {{background:{panel};border:1px solid {border};border-radius:5px;padding:7px;min-height:18px;}}
        QComboBox QAbstractItemView {{background:{panel};selection-background-color:#21766c;}}
        QTableView {{background:{panel};alternate-background-color:{alternate};border:0;selection-background-color:#1b5c59;selection-color:white;}}
        QTableView::item {{padding:7px;border-bottom:1px solid {border};}}
        QHeaderView::section {{background:{panel};color:{muted};border:0;border-bottom:1px solid {border};padding:10px;font-size:11px;}}
        QTextBrowser {{background:{panel};border:1px solid {border};border-radius:8px;padding:12px;}}
        QScrollArea {{background:transparent;}}
        QScrollBar:vertical {{width:9px;background:{bg};}}
        QScrollBar::handle:vertical {{background:{border};border-radius:4px;min-height:25px;}}
        QToolTip {{background:{panel};color:{text};border:1px solid {border};}}
        """)

    def navigate(self, name):
        if name:
            self.page = name
            self.rebuild_page()

    def change_workspace(self, index):
        self.mode = "demo" if index == 0 else "research"
        assets = self.store.assets(self.mode)
        self.active_symbol = assets[0]["symbol"] if assets else ""
        self.live_results = []
        self.rebuild_page()

    def rebuild_page(self):
        self.title.setText(self.page)
        self.subtitle.setText(
            SUBTITLES.get(self.page, "Source-attributed observations for independent investment research.")
        )
        self.banner.setText(
            "FICTIONAL DEMONSTRATION  ·  All SYN assets, prices and awards are synthetic training fixtures dated November 2025. They are not market observations."
            if self.mode == "demo"
            else "PERSONAL RESEARCH  ·  Limited local universe. Check timestamps and permissions. Missing data is unavailable, never zero evidence of activity."
        )
        body = QWidget()
        self.content = QVBoxLayout(body)
        self.content.setContentsMargins(0, 0, 5, 0)
        self.content.setSpacing(18)
        handlers = {
            "Dashboard": self.dashboard,
            "Technology Movers": self.movers,
            "Emerging Technology": self.emerging,
            "Cryptocurrency": self.crypto,
            "Unusual Options Activity": self.options,
            "Chart Analysis & Forecasts": self.chart_analysis,
            "Government Contracts": self.contracts,
            "Nancy Pelosi Tracker": lambda: self.politics("Nancy Pelosi"),
            "Donald Trump Tracker": lambda: self.politics("Donald Trump"),
            "Investment Opportunities": self.opportunities,
            "Watchlists": self.watchlists,
            "Paper Portfolio": self.portfolio,
            "Weekly Reports": self.weekly_reports,
            "Report Archive": self.archive,
            "Data Sources & Health": self.sources,
            "Settings": self.settings,
        }
        try:
            handlers[self.page]()
        except (ValueError, KeyError, TypeError) as exc:
            self.page_errors.append(f"{self.page}: {exc}")
            self.content.addWidget(
                label(
                    f"This data could not be analyzed: {exc}. Review the source data before continuing.",
                    "banner",
                )
            )
        self.content.addStretch()
        old = self.body_scroll.takeWidget()
        if old:
            old.deleteLater()
        self.body_scroll.setWidget(body)

    def add_note(self, text):
        self.content.addWidget(label(text, "muted"))

    def rows(self, kind=None):
        return asset_rows(self.store, self.mode, kind)

    def dashboard(self):
        equities, crypto = self.rows("equity"), self.rows("crypto")
        top = sorted(
            (a for a in equities if a.get("week_pct") is not None), key=lambda a: a["week_pct"], reverse=True
        )
        metrics = QHBoxLayout()
        values = [
            ("TECHNOLOGY UNIVERSE", str(len(equities)), "Local assets · coverage limited"),
            (
                "LEADING 5-PERIOD MOVER",
                f"{fmt(top[0]['week_pct'])}%" if top else "—",
                top[0]["symbol"] if top else "Import price history",
            ),
            ("CRYPTO ASSETS", str(len(crypto)), "Independent digital asset universe"),
            ("VERIFIED CANDIDATES", "0", "No validated buy recommendations"),
        ]
        for title, value, detail in values:
            frame, layout = card()
            layout.addWidget(label(title, "eyebrow"))
            layout.addWidget(label(value, "metric"))
            layout.addWidget(label(detail, "accent"))
            metrics.addWidget(frame, 1)
        self.content.addLayout(metrics)
        split = QHBoxLayout()
        frame, layout = card("Market lens")
        layout.addWidget(label("Selected local price history · drag to pan, wheel to zoom", "muted"))
        layout.addWidget(self.price_chart(self.active_symbol or (top[0]["symbol"] if top else ""), 245))
        split.addWidget(frame, 3)
        insight, inner = card("Research discipline")
        inner.addWidget(label("Evidence before conviction", "cardTitle"))
        inner.addWidget(
            label(
                "01   Check source freshness\n\n02   Seek independent confirmation\n\n03   Record contradictory evidence\n\n04   Abstain when the thesis is incomplete"
            )
        )
        inner.addStretch()
        inner.addWidget(button("Explore research candidates →", lambda: self.nav.setCurrentRow(9)))
        split.addWidget(insight, 1)
        self.content.addLayout(split)
        frame, layout = card("Technology watch · 5-period performance")
        layout.addWidget(
            table(
                top[:6],
                [
                    ("ASSET", "symbol"),
                    ("COMPANY", "name"),
                    ("PRICE $", "price"),
                    ("1P %", "day_pct"),
                    ("5P %", "week_pct"),
                    ("21P %", "month_pct"),
                    ("REL. VOL", "relative_volume"),
                    ("PRICE AS OF", "bar_as_of"),
                ],
                265,
            )
        )
        self.content.addWidget(frame)
        self.add_note(
            "Returns describe the imported observation cadence. US daily equities: 5/21 sessions approximate week/month. This is not a complete market screener."
        )

    def price_chart(self, symbol, height=330):
        chart = pg.PlotWidget(axisItems={"bottom": pg.DateAxisItem(utcOffset=0)})
        chart.setBackground(self.colors["panel"])
        chart.setFixedHeight(height)
        chart.showGrid(x=False, y=True, alpha=0.12)
        chart.setLabel("left", "Price", units="USD", color=self.colors["muted"])
        chart.setMenuEnabled(False)
        for axis in ("left", "bottom"):
            chart.getAxis(axis).setTextPen(self.colors["muted"])
            chart.getAxis(axis).setPen(self.colors["border"])
        bars = self.store.bars(self.mode, symbol)
        if bars:
            times = [datetime.fromisoformat(b["date"]).replace(tzinfo=timezone.utc).timestamp() for b in bars]
            close = [b["close"] for b in bars]
            chart.plot(times, close, pen=pg.mkPen("#39c7b1", width=2), name="Close")
            if len(bars) >= 20:
                ma = [sum(close[i - 19 : i + 1]) / 20 for i in range(19, len(close))]
                chart.plot(
                    times[19:],
                    ma,
                    pen=pg.mkPen("#8194e5", width=1.3, style=Qt.PenStyle.DashLine),
                    name="SMA20",
                )
            crosshair = pg.InfiniteLine(
                angle=90, movable=False, pen=pg.mkPen("#687d94", style=Qt.PenStyle.DotLine)
            )
            chart.addItem(crosshair, ignoreBounds=True)
            chart.scene().sigMouseMoved.connect(
                lambda position: crosshair.setPos(chart.plotItem.vb.mapSceneToView(position).x())
            )
            chart.setTitle(f"{symbol}  ·  close / SMA20", color=self.colors["muted"], size="11pt")
        else:
            chart.setTitle(
                "No price history · import an authorized daily OHLCV CSV", color=self.colors["muted"]
            )
        return chart

    def movers(self, crypto=False):
        rows = self.rows("crypto" if crypto else "equity")
        frame, layout = card("Digital asset explorer" if crypto else "Technology universe explorer")
        controls = QHBoxLayout()
        search = QLineEdit()
        search.setPlaceholderText("Search symbol, name or category…")
        search.setAccessibleName("Search assets")
        category = QComboBox()
        category.addItems(["All categories"] + sorted({a.get("category", "Unclassified") for a in rows}))
        cap = QComboBox()
        cap.addItems(["Any market cap", "Above $1B", "Above $10B", "Below $1B"])
        liquidity = QComboBox()
        liquidity.addItems(["Any latest $ volume", "Above $1M", "Above $10M"])
        for control in (search, category, cap, liquidity):
            controls.addWidget(control)
        layout.addLayout(controls)
        holder = QVBoxLayout()
        layout.addLayout(holder)

        def update():
            while holder.count():
                item = holder.takeAt(0)
                if item is not None:
                    child = item.widget()
                    if child is not None:
                        child.deleteLater()
            selected = []
            for a in rows:
                if (
                    search.text().lower()
                    not in " ".join(str(a.get(k, "")) for k in ("symbol", "name", "category")).lower()
                ):
                    continue
                if category.currentIndex() and a.get("category") != category.currentText():
                    continue
                c, liq = a.get("market_cap"), a.get("liquidity_usd")
                if cap.currentIndex() and (
                    c is None
                    or (cap.currentIndex() == 1 and c < 1e9)
                    or (cap.currentIndex() == 2 and c < 1e10)
                    or (cap.currentIndex() == 3 and c >= 1e9)
                ):
                    continue
                if liquidity.currentIndex() and (
                    liq is None or liq < (1e6 if liquidity.currentIndex() == 1 else 1e7)
                ):
                    continue
                selected.append(a)
            selected.sort(key=lambda a: a.get("week_pct") or 0, reverse=True)
            grid = table(
                selected,
                [
                    ("ASSET", "symbol"),
                    ("NAME", "name"),
                    ("CATEGORY", "category"),
                    ("PRICE $", "price"),
                    ("1P %", "day_pct"),
                    ("5P %", "week_pct"),
                    ("21P %", "month_pct"),
                    ("REL VOL", "relative_volume"),
                    ("MKT CAP $", "market_cap"),
                    ("Δ CAP EST. $", "cap_change_estimate"),
                    ("AS OF", "bar_as_of"),
                ],
                430,
            )
            grid.cellDoubleClicked.connect(lambda r, c: self.open_chart(grid.item(r, 0).text()))
            holder.addWidget(grid)

        search.textChanged.connect(update)
        for combo in (category, cap, liquidity):
            combo.currentIndexChanged.connect(update)
        update()
        layout.addWidget(
            label(
                "Double-click an asset to inspect its chart. Relative volume compares the latest bar with the preceding 20. Market-cap change is estimated only when shares outstanding are supplied; it is not a verified corporate-action-adjusted change.",
                "muted",
            )
        )
        self.content.addWidget(frame)

    def emerging(self):
        groups: dict[str, list[dict]] = {}
        for row in self.rows("equity"):
            groups.setdefault(row.get("category", "Unclassified"), []).append(row)
        rows = []
        for category, members in groups.items():
            eligible = [a["week_pct"] for a in members if a.get("week_pct") is not None]
            rows.append(
                {
                    "category": category,
                    "assets": len(members),
                    "avg_pct": sum(eligible) / len(eligible) if eligible else None,
                    "symbols": ", ".join(a["symbol"] for a in members),
                }
            )
        frame, layout = card("Emerging technology map")
        layout.addWidget(
            table(
                rows,
                [
                    ("TECHNOLOGY", "category"),
                    ("LOCAL ASSETS", "assets"),
                    ("EQUAL-WEIGHT 5P %", "avg_pct"),
                    ("UNIVERSE", "symbols"),
                ],
                380,
            )
        )
        layout.addWidget(
            label(
                "These are local-universe averages, not sector indices. A one-company category cannot establish sector outperformance. Category assignments are user-supplied.",
                "muted",
            )
        )
        self.content.addWidget(frame)

    def crypto(self):
        self.movers(crypto=True)
        frame, layout = card("Cross-market correlation")
        assets = self.rows()
        eq, cr = (
            [a["symbol"] for a in assets if a["kind"] == "equity"],
            [a["symbol"] for a in assets if a["kind"] == "crypto"],
        )
        controls = QHBoxLayout()
        a, b = QComboBox(), QComboBox()
        a.addItems(eq)
        b.addItems(cr)
        result = label("Select two assets with at least 30 aligned return intervals.", "muted")

        def calculate():
            value, n = correlations(self.store, self.mode, a.currentText(), b.currentText())
            result.setText(
                f"Pearson return correlation: {fmt(value, 3)} · {n} aligned intervals. Descriptive only; changing correlation does not imply causation."
            )

        controls.addWidget(a)
        controls.addWidget(b)
        controls.addWidget(button("Compare", calculate))
        layout.addLayout(controls)
        layout.addWidget(result)
        layout.addWidget(
            label(
                "Bitcoin dominance unavailable: the local universe does not establish total global crypto capitalization. Stablecoins and memecoins are separated only when explicitly classified by the imported metadata.",
                "muted",
            )
        )
        self.content.addWidget(frame)

    def options(self):
        observations = self.store.records(self.mode, "options")
        rows = []
        for record in observations:
            metrics = option_metrics(record)
            rows.append(record | {"metrics": metrics})
        frame, layout = card("Options observations · coverage-limited")
        layout.addWidget(
            label(
                "Trade intent unknown. A call or put may be part of a hedge, spread or closing position. No institutional or insider attribution is made.",
                "muted",
            )
        )
        grid = table(
            rows,
            [
                ("ASSET", "symbol"),
                ("TYPE", "option_type"),
                ("RECORD", "record_type"),
                ("DATE", "date"),
                ("EXPIRY", "expiry"),
                ("STRIKE", "strike"),
                ("CONTRACTS", "size"),
                ("VOLUME", "volume"),
                ("OPEN INTEREST", "open_interest"),
                ("SOURCE", "source"),
            ],
            330,
        )
        grid.cellDoubleClicked.connect(
            lambda r, c: self.show_record(
                "Options evidence", self._row_record(grid, r, observations, "symbol")
            )
        )
        layout.addWidget(grid)
        for row in rows[:15]:
            layout.addWidget(
                label(row["symbol"] + " · " + json.dumps(row["metrics"], ensure_ascii=False), "muted")
            )
        layout.addWidget(
            label(
                "Premium is estimated only for an observed individual trade using actual size × price × multiplier. Aggregate volume × last price is never substituted. A volume anomaly is not directional evidence. Corporate-event linkage requires a verified event calendar (not connected).",
                "muted",
            )
        )
        self.content.addWidget(frame)

    def _row_record(self, grid, row, records, key):
        selected = grid.record(row)
        return [r for r in records if selected is not None and r.get(key) == selected.get(key)]

    def open_chart(self, symbol):
        self.active_symbol = symbol
        if self.nav.currentRow() == 5:
            self.rebuild_page()
        else:
            self.nav.setCurrentRow(5)

    def chart_analysis(self):
        controls = QHBoxLayout()
        chooser = QComboBox()
        chooser.addItems([a["symbol"] for a in self.store.assets(self.mode)])
        chooser.setCurrentText(self.active_symbol)
        controls.addWidget(label("Analyze asset"))
        controls.addWidget(chooser, 1)
        controls.addWidget(button("Add / remove watchlist", lambda: self.toggle_watch(chooser.currentText())))
        self.content.addLayout(controls)
        chart_area = QWidget()
        chart_layout = QVBoxLayout(chart_area)
        chart_layout.setContentsMargins(0, 0, 0, 0)

        def refresh():
            while chart_layout.count():
                item = chart_layout.takeAt(0)
                if item is not None:
                    child = item.widget()
                    if child is not None:
                        child.deleteLater()
            symbol = chooser.currentText()
            self.active_symbol = symbol
            bars = self.store.bars(self.mode, symbol)
            frame, layout = card("Price structure")
            layout.addWidget(self.price_chart(symbol, 340))
            chart_layout.addWidget(frame)
            if not bars:
                chart_layout.addWidget(
                    label("Import chronological daily OHLCV data to calculate indicators.", "muted")
                )
                return
            ind = indicators(bars)
            frame, layout = card("Indicators · latest observation")
            layout.addWidget(
                table(
                    [{"indicator": k, "value": v} for k, v in ind.items() if not isinstance(v, list)],
                    [("INDICATOR", "indicator"), ("VALUE", "value")],
                    260,
                )
            )
            chart_layout.addWidget(frame)
            patterns = detect_patterns(bars)
            frame, layout = card("Conditional scenarios & validation")
            layout.addWidget(
                label(
                    "Forecast: ABSTAIN · Confidence unavailable · Validated samples: 0. Pattern labels describe objective chart geometry; predictive reliability has not been established.",
                    "banner",
                )
            )
            for pattern in patterns:
                layout.addWidget(
                    label(
                        f"{pattern['name']} · {pattern.get('direction', 'neutral')} · {pattern.get('evidence', '')}"
                    )
                )
            if not patterns:
                layout.addWidget(label("No supported pattern meets the detector criteria."))
            layout.addWidget(
                label(
                    "Bullish: sustained close above measured resistance with volume confirmation merits investigation. Bearish: a close below support weakens the structure. Neutral: remain uncommitted while price consolidates. No target price or entry recommendation is inferred.",
                    "muted",
                )
            )
            layout.addWidget(
                button(
                    "Evaluate fixed SMA rule on this history",
                    lambda: self.show_record("Chronological research diagnostic", walk_forward(bars)),
                )
            )
            layout.addWidget(
                label(
                    "This diagnostic uses one predeclared rule and costs, not pattern validation or calibrated forecasts. Synthetic history cannot validate an investment strategy.",
                    "muted",
                )
            )
            chart_layout.addWidget(frame)

        chooser.currentTextChanged.connect(refresh)
        refresh()
        self.content.addWidget(chart_area)

    def contracts(self):
        rows = self.store.records(self.mode, "contracts")
        frame, layout = card("Government award intelligence")
        layout.addWidget(
            label(
                "Award ceilings, obligated funding and realized revenue are different measures. Reimporting the same award ID updates its observation; values are never blindly summed.",
                "muted",
            )
        )
        grid = table(
            rows,
            [
                ("AWARD ID", "id"),
                ("COMPANY", "company"),
                ("TICKER", "ticker"),
                ("AGENCY", "agency"),
                ("COUNTRY", "country"),
                ("STATUS", "status"),
                ("CEILING $", "ceiling"),
                ("OBLIGATED $", "obligated"),
                ("AWARD DATE", "award_date"),
            ],
            340,
        )
        grid.cellDoubleClicked.connect(
            lambda r, c: self.show_record(
                "Contract report · original evidence", self._row_record(grid, r, rows, "id")
            )
        )
        layout.addWidget(grid)
        assets = {a["symbol"]: a for a in self.store.assets(self.mode)}
        for record in rows[:10]:
            asset = assets.get(record.get("ticker"), {})
            layout.addWidget(
                label(
                    f"{record['company']} · {json.dumps(contract_metrics(record, asset.get('revenue') or None, asset.get('market_cap') or None), ensure_ascii=False)}",
                    "muted",
                )
            )
        layout.addWidget(
            label(
                "Double-click an award for government, purpose, dates, duration, technology, possible expansion, assumptions, risks and source. Missing fields remain not disclosed. Subsidiary/subcontractor and ticker relationships require manual source verification.",
                "muted",
            )
        )
        self.content.addWidget(frame)

    def politics(self, person):
        frame, layout = card(f"{person} · disclosure research")
        layout.addWidget(
            label(
                "AUTOMATED COLLECTION DISABLED · Official disclosure records have statutory use restrictions. No actual political records are bundled. Import only records you are lawfully permitted to use, retain and export.",
                "banner",
            )
        )
        rows = []
        for record in self.store.records(self.mode, "disclosures"):
            if record["person"] == person:
                perf, start = disclosure_performance(self.store, self.mode, record)
                rows.append(record | {"performance_pct": perf, "measurement_start": start})
        grid = table(
            rows,
            [
                ("RECORD", "id"),
                ("ASSET", "asset"),
                ("OWNER", "owner"),
                ("TRANSACTION", "transaction_type"),
                ("TRADE DATE", "transaction_date"),
                ("PUBLICATION", "publication_date"),
                ("RANGE LOW $", "value_min"),
                ("RANGE HIGH $", "value_max"),
                ("POST-PUB %", "performance_pct"),
            ],
            330,
        )
        grid.cellDoubleClicked.connect(
            lambda r, c: self.show_record("Disclosure evidence", self._row_record(grid, r, rows, "id"))
        )
        layout.addWidget(grid)
        layout.addWidget(
            button(
                "Open official source",
                lambda: QDesktopServices.openUrl(
                    QUrl(
                        "https://disclosures-clerk.house.gov/FinancialDisclosure"
                        if person == "Nancy Pelosi"
                        else "https://www.oge.gov/web/oge.nsf/Officials%20Individual%20Disclosures%20Search%20Collection?OpenForm"
                    )
                ),
            )
        )
        layout.addWidget(
            label(
                "Personal, spouse, dependent and associated ownership remain separate. Disclosed ranges are not exact transaction sizes. Post-publication return uses the first available close strictly after publication because publication time is unknown; no copying strategy or earlier access is assumed. Donations, policies, affiliated businesses and third-party portfolios are not personal transactions.",
                "muted",
            )
        )
        self.content.addWidget(frame)

    def opportunities(self):
        rows = [opportunity(self.store, self.mode, a) for a in self.rows("equity")]
        rows.sort(key=lambda a: a["score"] if a["score"] is not None else -1, reverse=True)
        visible = [r | {"coverage_pct": r["coverage"] * 100} for r in rows]
        frame, layout = card("Evidence-ranked research queue")
        layout.addWidget(
            label(
                "NO VALIDATED BUY RECOMMENDATION · Scores are configurable priorities, not probabilities or price targets. Current evidence can justify observing rather than investing.",
                "banner",
            )
        )
        grid = table(
            visible,
            [
                ("ASSET", "symbol"),
                ("COMPANY", "name"),
                ("HEURISTIC /100", "score"),
                ("COVERAGE %", "coverage_pct"),
                ("DECISION", "decision"),
                ("MISSING", "missing"),
            ],
            330,
        )
        grid.cellDoubleClicked.connect(
            lambda r, c: self.show_record(
                "Research thesis · supporting and contradictory evidence",
                self._row_record(grid, r, rows, "symbol"),
            )
        )
        layout.addWidget(grid)
        layout.addWidget(
            label(
                "Double-click for evidence, bullish/bearish/neutral scenarios, entry conditions, horizon and invalidation. Fundamentals, political and directional options scores are withheld until defensible independent criteria and data exist. A low stock price or P/E alone does not establish undervaluation.",
                "muted",
            )
        )
        self.content.addWidget(frame)

    def toggle_watch(self, symbol):
        try:
            self.store.toggle_watch(self.mode, symbol)
            self.status.setText(f"Watchlist updated · {symbol}")
            if self.page == "Watchlists":
                self.rebuild_page()
        except ValueError as exc:
            self.error(str(exc))

    def watchlists(self):
        controls = QHBoxLayout()
        chooser = QComboBox()
        chooser.addItems([a["symbol"] for a in self.store.assets(self.mode)])
        controls.addWidget(chooser, 1)
        controls.addWidget(button("Add / remove", lambda: self.toggle_watch(chooser.currentText())))
        self.content.addLayout(controls)
        selected = set(self.store.watchlist(self.mode))
        frame, layout = card("Your watchlist")
        layout.addWidget(
            table(
                [a for a in self.rows() if a["symbol"] in selected],
                [
                    ("ASSET", "symbol"),
                    ("NAME", "name"),
                    ("PRICE $", "price"),
                    ("1P %", "day_pct"),
                    ("5P %", "week_pct"),
                    ("AS OF", "bar_as_of"),
                ],
                300,
            )
        )
        self.content.addWidget(frame)
        frame, layout = card("Local alert threshold")
        threshold = QDoubleSpinBox()
        threshold.setRange(0.1, 100)
        threshold.setValue(self.store.setting(f"alert_{self.mode}", 5.0))
        threshold.setSuffix("% absolute 1-period move")
        layout.addWidget(threshold)
        layout.addWidget(button("Save & evaluate alert", lambda: self.evaluate_alert(threshold.value())))
        layout.addWidget(
            label(
                "Evaluates the latest stored observation of watched assets. No background data feed or push service; stale dates are shown explicitly.",
                "muted",
            )
        )
        self.content.addWidget(frame)

    def evaluate_alert(self, threshold):
        self.store.set_setting(f"alert_{self.mode}", threshold)
        watched = set(self.store.watchlist(self.mode))
        triggered = [
            a
            for a in self.rows()
            if a["symbol"] in watched and a.get("day_pct") is not None and abs(a["day_pct"]) >= threshold
        ]
        self.show_record(
            "Local alert results · latest stored observations",
            triggered or {"status": "No threshold crossings in stored watched data"},
        )

    def portfolio(self):
        controls = QHBoxLayout()
        controls.addWidget(label("Manual, long-only paper ledger. No order execution.", "muted"), 1)
        controls.addWidget(button("Record paper trade", self.paper_dialog, True))
        self.content.addLayout(controls)
        frame, layout = card("Paper positions · marks from latest stored closes")
        rows = [
            {
                k: float(v) if k in {"quantity", "net_cost", "mark", "value", "pnl"} and v is not None else v
                for k, v in r.items()
            }
            for r in self.store.paper_positions(self.mode)
        ]
        layout.addWidget(
            table(
                rows,
                [
                    ("ASSET", "symbol"),
                    ("QUANTITY", "quantity"),
                    ("NET CASH COST $", "net_cost"),
                    ("MARK $", "mark"),
                    ("VALUE $", "value"),
                    ("TOTAL P/L $", "pnl"),
                    ("MARK DATE", "as_of"),
                ],
                250,
            )
        )
        layout.addWidget(
            label(
                "Total P/L = remaining market value − net cash paid including fees. Closed positions retain realized net P/L. No claim of recommendation performance, total account return or cash-flow-matched benchmark alpha is made.",
                "muted",
            )
        )
        self.content.addWidget(frame)
        frame, layout = card("Chronological transaction ledger")
        layout.addWidget(
            table(
                self.store.paper_trades(self.mode),
                [
                    ("DATE", "date"),
                    ("ASSET", "symbol"),
                    ("SIDE", "side"),
                    ("QUANTITY", "quantity"),
                    ("PRICE $", "price"),
                    ("FEE $", "fee"),
                ],
                250,
            )
        )
        self.content.addWidget(frame)
        benchmarks = [a for a in self.rows("benchmark")]
        if benchmarks:
            self.add_note(
                "Reference only (unmatched cash flows): "
                + "; ".join(f"{b['symbol']} 21-period return {fmt(b.get('month_pct'))}%" for b in benchmarks)
            )
        else:
            self.add_note(
                "Benchmark unavailable. Import a suitable benchmark with kind=benchmark. Matched portfolio attribution remains deferred."
            )

    def paper_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Record simulated transaction")
        layout = QFormLayout(dialog)
        symbol, side = QComboBox(), QComboBox()
        symbol.addItems([a["symbol"] for a in self.store.assets(self.mode)])
        side.addItems(["buy", "sell"])
        quantity, price, fee = QLineEdit("1"), QLineEdit("100"), QLineEdit("0")
        when = QLineEdit(date.today().isoformat())
        for title, control in [
            ("Asset", symbol),
            ("Side", side),
            ("Quantity", quantity),
            ("Actual simulated fill price", price),
            ("Fee", fee),
            ("Date (YYYY-MM-DD)", when),
        ]:
            layout.addRow(title, control)
        layout.addRow(
            label("Use an explicit simulated fill price. Historical closes are not assumed executable.")
        )
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addRow(buttons)
        buttons.rejected.connect(dialog.reject)

        def save():
            try:
                self.store.paper_trade(
                    self.mode,
                    symbol.currentText(),
                    side.currentText(),
                    quantity.text(),
                    price.text(),
                    fee.text(),
                    when.text(),
                )
            except ValueError as exc:
                self.error(str(exc))
                return
            dialog.accept()
            self.rebuild_page()

        buttons.accepted.connect(save)
        dialog.exec()

    def weekly_reports(self):
        frame, layout = card("Weekly intelligence briefing")
        sections = QComboBox()
        sections.addItems(["Full report"] + SECTIONS)
        layout.addWidget(sections)
        controls = QHBoxLayout()
        controls.addWidget(
            button("Preview & archive locally", lambda: self.generate_report(sections.currentText()), True)
        )
        controls.addWidget(
            button(
                "Export PDF / HTML / CSV / JSON",
                lambda: self.save_report(
                    snapshot(
                        self.store,
                        self.mode,
                        None if sections.currentIndex() == 0 else sections.currentText(),
                    )
                ),
            )
        )
        layout.addLayout(controls)
        enabled = QCheckBox(
            "Generate Monday 08:00 local briefing while the app is open; catch up on next launch"
        )
        enabled.setChecked(self.store.setting(f"weekly_{self.mode}", False))
        enabled.toggled.connect(lambda value: self.store.set_setting(f"weekly_{self.mode}", value))
        layout.addWidget(enabled)
        layout.addWidget(
            label(
                "Uses this computer's local timezone and stored data. Does not refresh the market feed. Catch-up creates the latest due briefing, not fabricated historical reports. Full/individual reports retain timestamps, data gaps and methodology.",
                "muted",
            )
        )
        self.content.addWidget(frame)
        for i, title in enumerate(SECTIONS, 1):
            self.content.addWidget(label(f"{i:02}   {title}", "muted"))

    def generate_report(self, selected="Full report"):
        report = snapshot(self.store, self.mode, None if selected == "Full report" else selected)
        self.store.archive_report(self.mode, report["title"], report)
        self.preview_report(report)
        self.status.setText(
            "Report archived locally · contains stored observations, not a refreshed market feed"
        )

    def check_schedule(self):
        if self.closed or self.recovery_busy:
            return
        now = datetime.now().astimezone()
        monday = now.date() - timedelta(days=now.weekday())
        if now.weekday() == 0 and now.hour < 8:
            monday -= timedelta(days=7)
        due = monday.isoformat()
        for mode in ("demo", "research"):
            if (
                self.store.setting(f"weekly_{mode}", False)
                and self.store.setting(f"last_weekly_{mode}") != due
            ):
                report = snapshot(self.store, mode)
                report["due_week"] = due
                self.store.archive_report(mode, report["title"] + " · " + due, report)
                self.store.set_setting(f"last_weekly_{mode}", due)
                self.status.setText(
                    f"Weekly briefing archived · {mode} · week of {due} · stored-data snapshot"
                )

    def archive(self):
        records = self.store.reports(self.mode)
        frame, layout = card("Local report archive")
        grid = table(
            records,
            [("ID", "id"), ("GENERATED AT", "created_at"), ("REPORT", "title"), ("WORKSPACE", "mode")],
            380,
        )

        def open_report(r, c):
            row = grid.record(r)
            if row:
                self.preview_report(json.loads(row["payload"]))

        grid.cellDoubleClicked.connect(open_report)
        layout.addWidget(grid)
        layout.addWidget(
            label(
                "Double-click to preview and export the original immutable snapshot. Reports remain on this computer.",
                "muted",
            )
        )
        self.content.addWidget(frame)

    def preview_report(self, report):
        dialog = QDialog(self)
        dialog.setWindowTitle("TechPulse · report preview")
        dialog.resize(1040, 760)
        layout = QVBoxLayout(dialog)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(False)
        browser.setHtml(html_text(report))
        layout.addWidget(browser)
        controls = QHBoxLayout()
        controls.addWidget(button("Export report", lambda: self.save_report(report), True))
        controls.addWidget(button("Close", dialog.accept))
        layout.addLayout(controls)
        dialog.exec()

    def save_report(self, report):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export authorized research report",
            str(data_directory() / "techpulse-report.html"),
            "HTML (*.html);;PDF (*.pdf);;CSV (*.csv);;JSON (*.json)",
        )
        if path:
            try:
                export_report(report, path)
                self.status.setText("Exported " + path)
            except (OSError, ValueError) as exc:
                self.error(str(exc))

    def sources(self):
        rows = self.rows()
        frame, layout = card("Local data health & provenance")
        layout.addWidget(
            table(
                rows,
                [
                    ("ASSET", "symbol"),
                    ("OBSERVATIONS", "data_points"),
                    ("PRICE AS OF", "bar_as_of"),
                    ("PRICE SOURCE", "price_source"),
                    ("PRICE SOURCE URL", "price_source_url"),
                    ("PRICE FETCHED AT", "price_fetched_at"),
                    ("COVERAGE", "coverage"),
                ],
                300,
            )
        )
        self.content.addWidget(frame)
        frame, layout = card("Optional official provider previews · session memory only")
        layout.addWidget(
            label(
                "No requests are made until you choose a provider. Preview data is excluded from the database, report archive, backups and exports. These are bounded snapshots, not continuous feeds. Use each provider only as your own terms permit.",
                "muted",
            )
        )
        for name, callback in [
            ("Preview CoinGecko Demo · top 100", self.fetch_crypto),
            ("Preview Alpaca IEX daily bars", self.fetch_equities),
            ("Search USAspending awards", self.fetch_contracts),
            ("Preview SEC annual fundamentals", self.fetch_sec),
            ("Open SEC companyfacts JSON locally", self.open_sec_json),
        ]:
            layout.addWidget(button(name, callback))
        layout.addWidget(
            label(
                "Optional environment variables: COINGECKO_DEMO_API_KEY; ALPACA_API_KEY and ALPACA_SECRET_KEY. No key is required for offline imports or USAspending. CoinGecko attribution: Data provided by CoinGecko · https://www.coingecko.com/en/api. IEX is a limited exchange feed; free options are not comprehensive OPRA.",
                "muted",
            )
        )
        self.content.addWidget(frame)
        if self.live_results and any("metrics" in r for r in self.live_results):
            frame, layout = card("SEC annual fundamentals · inspect full facts for periods/accessions")
            layout.addWidget(
                table(
                    self.live_results,
                    [
                        ("FILER", "name"),
                        ("CUTOFF", "as_of"),
                        ("REVENUE GROWTH %", "revenue_growth_pct"),
                        ("NET MARGIN %", "net_margin_pct"),
                        ("FCF USD", "free_cash_flow_usd"),
                        ("FCF PERIOD END", "free_cash_flow_period_end"),
                        ("FCF MARGIN %", "fcf_margin_pct"),
                    ],
                    180,
                )
            )
            layout.addWidget(
                label(
                    "US-GAAP annual USD facts only. Current SEC aggregates are not a guaranteed historical archive. Missing or unmatched periods remain unavailable. No score or ticker mapping is inferred.",
                    "muted",
                )
            )
            self.content.addWidget(frame)
        if self.live_results:
            frame, layout = card("Latest provider preview · unretained")
            layout.addWidget(
                button(
                    "Inspect session-only observations",
                    lambda: self.show_record(
                        "Provider preview · do not redistribute restricted data", self.live_results
                    ),
                )
            )
            layout.addWidget(
                table(
                    self.live_results[:100],
                    [
                        ("ASSET / AWARD", "symbol"),
                        ("NAME / COMPANY", "name"),
                        ("PRICE $", "price"),
                        ("AS OF", "as_of"),
                        ("SOURCE", "source"),
                        ("COVERAGE", "coverage"),
                    ],
                    300,
                )
            )
            self.content.addWidget(frame)
        self.add_note(
            "SEC annual fundamentals are filing-date-filtered previews; FRED, SAM.gov and TED remain planned. Corporate/agency announcements and earnings require verified imports. Political automated collection remains disabled; public visibility does not grant unrestricted use."
        )

    def run_provider(self, title, fn):
        if self.worker or self.recovery_busy:
            self.error("A provider request is already running")
            return
        if self.mode != "research":
            self.workspace.setCurrentIndex(1)
        self.live_results = []
        self.rebuild_page()
        self.status.setText(title + " · requesting official endpoint…")
        worker = Worker(fn)
        self.worker = worker

        def success(rows):
            self.worker = None
            if self.mode != "research":
                self.live_results = []
                self.status.setText(title + " · response discarded after workspace change")
                return
            self.live_results = rows
            self.status.setText(f"{title} · {len(rows)} session-only observations · {utc_now()}")
            if self.page == "Data Sources & Health":
                self.rebuild_page()

        def failed(message):
            self.worker = None
            self.live_results = []
            self.status.setText(title + " · failed; no demo or stale result substituted")
            self.error(message)

        worker.signals.success.connect(success)
        worker.signals.failed.connect(failed)
        QThreadPool.globalInstance().start(worker)

    def fetch_sec(self):
        from .sec import SECProvider

        contact = self.sec_user_agent or os.environ.get("SEC_USER_AGENT", "")
        if not contact:
            self.error(
                "Add your real SEC contact in Settings for this session, or set SEC_USER_AGENT before launch. No API key required. You can also open a companyfacts JSON locally."
            )
            return
        raw, ok = QInputDialog.getText(
            self,
            "SEC annual fundamentals",
            "Ticker or CIK, optionally followed by comma and cutoff YYYY-MM-DD",
        )
        if not ok:
            return
        try:
            fields = [v.strip() for v in raw.split(",")]
            if not 1 <= len(fields) <= 2:
                raise ValueError("Enter ticker/CIK, optionally followed by YYYY-MM-DD")
            identifier = fields[0].upper()
            if not identifier:
                raise ValueError("Enter a ticker or CIK")
            cutoff = date.fromisoformat(fields[1]) if len(fields) == 2 else date.today()
            if cutoff > date.today():
                raise ValueError("Filing cutoff cannot be in the future")
        except ValueError as exc:
            self.error(str(exc))
            return

        def fetch():
            with SECProvider(contact) as provider:
                return provider.fundamentals_for(identifier, cutoff.isoformat())

        self.run_provider("SEC EDGAR annual fundamentals", fetch)

    def open_sec_json(self):
        from .sec import normalize_company_facts

        if self.worker or self.recovery_busy:
            self.error("Wait for the active provider request to finish")
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "Open official SEC companyfacts JSON · session only", "", "JSON (*.json)"
        )
        if not path:
            return
        cutoff, ok = QInputDialog.getText(
            self,
            "Filing cutoff",
            "Use only filings strictly before YYYY-MM-DD",
            text=date.today().isoformat(),
        )
        if not ok:
            return
        try:
            source = Path(path)
            if source.stat().st_size > 8 * 1024 * 1024:
                raise ValueError("SEC JSON exceeds 8 MiB; choose a smaller companyfacts file")
            result = normalize_company_facts(json.loads(source.read_text(encoding="utf-8-sig")), cutoff)
        except (OSError, ValueError, TypeError, RecursionError) as exc:
            self.error(str(exc))
            return
        if self.mode != "research":
            self.workspace.setCurrentIndex(1)
        result["input_origin"] = (
            "User-provided JSON; authenticity not verified; fetched_at is normalization time"
        )
        self.live_results = [result]
        self.rebuild_page()
        self.status.setText(
            "SEC JSON normalized locally · user-provided file authenticity unverified · not retained"
        )

    def fetch_crypto(self):
        from .providers import CoinGeckoProvider

        key = os.environ.get("COINGECKO_DEMO_API_KEY", "")
        if not key:
            self.error(
                "Set COINGECKO_DEMO_API_KEY in your environment and restart. Demo terms restrict commercial use, retention and redistribution; this preview remains in memory."
            )
            return

        def fetch():
            with CoinGeckoProvider(key) as provider:
                return provider.markets()

        self.run_provider("CoinGecko Demo", fetch)

    def fetch_equities(self):
        from .providers import AlpacaProvider

        key, secret = os.environ.get("ALPACA_API_KEY", ""), os.environ.get("ALPACA_SECRET_KEY", "")
        if not key or not secret:
            self.error(
                "Set ALPACA_API_KEY and ALPACA_SECRET_KEY in the environment and restart. Only the read-only data API is used."
            )
            return
        raw, ok = QInputDialog.getText(
            self, "Alpaca IEX preview", "Up to 10 comma-separated US symbols", text="AAPL,MSFT"
        )
        if ok:
            symbols = [s.strip().upper() for s in raw.split(",") if s.strip()]
            if not 1 <= len(symbols) <= 10:
                self.error("Choose 1–10 symbols")
                return

            def fetch():
                with AlpacaProvider(key, secret) as provider:
                    data = provider.daily_bars(
                        symbols,
                        (date.today() - timedelta(days=100)).isoformat(),
                        (date.today() - timedelta(days=1)).isoformat(),
                    )
                return [
                    {
                        "symbol": symbol,
                        "name": symbol,
                        "price": bars[-1]["close"] if bars else None,
                        "as_of": bars[-1]["date"] if bars else None,
                        "source": "Alpaca IEX",
                        "coverage": "Limited IEX daily preview",
                        "bars": bars,
                    }
                    for symbol, bars in data.items()
                ]

            self.run_provider("Alpaca IEX", fetch)

    def fetch_contracts(self):
        from .providers import USAspendingProvider

        keyword, ok = QInputDialog.getText(
            self, "USAspending award search", "Company or award keyword (ticker mapping is not inferred)"
        )
        if ok and keyword.strip():

            def fetch():
                with USAspendingProvider() as provider:
                    return [
                        r | {"symbol": r["award_id"], "name": r["company"], "as_of": r["award_date"]}
                        for r in provider.search(keyword.strip())
                    ]

            self.run_provider("USAspending", fetch)

    def set_sec_contact(self, value):
        from .providers import ProviderError
        from .sec import declared_user_agent

        try:
            contact = declared_user_agent(value) if value.strip() else ""
        except ProviderError as exc:
            self.error(str(exc))
            return False
        self.sec_user_agent = contact
        self.status.setText(
            "SEC contact set for this session only"
            if contact
            else "SEC session contact cleared; environment fallback applies"
        )
        return True

    def settings(self):
        frame, layout = card("Appearance & local storage")
        theme = QComboBox()
        theme.addItems(["dark", "light"])
        theme.setCurrentText(self.theme)

        def change(value):
            self.theme = value
            self.store.set_setting("theme", value)
            self.apply_theme()

        theme.currentTextChanged.connect(change)
        layout.addWidget(theme)
        layout.addWidget(
            label(
                f"Local database: {self.store.path}\nNo telemetry. No runtime LLM. Credentials are not written to SQLite.",
                "muted",
            )
        )
        layout.addWidget(button("Create SQLite backup", self.backup))
        layout.addWidget(button("Inspect and restore SQLite backup", self.restore_backup_dialog))
        layout.addWidget(
            label(
                "Restore replaces both workspaces, paper trades, reports and settings. A copy of the current database is saved first. Close other TechPulse windows before restoring; concurrent edits are not covered by that safety copy.",
                "muted",
            )
        )
        if self.last_recovery_point:
            layout.addWidget(label("Previous state saved at: " + self.last_recovery_point, "muted"))
        self.content.addWidget(frame)
        frame, layout = card("SEC access · contact for this session")
        contact = QLineEdit(self.sec_user_agent)
        contact.setObjectName("secContact")
        contact.setAccessibleName("SEC application name and contact email")
        contact.setPlaceholderText("Your application name and real contact email")
        contact.setMaxLength(256)
        layout.addWidget(contact)
        layout.addWidget(
            label(
                "Sent to the SEC in the User-Agent header when you request live SEC data. Kept in memory only; not written to SQLite, reports, backups or Windows settings. Use your real contact. Leaving blank restores SEC_USER_AGENT from the environment, if configured. Changing this field does not cancel an active request.",
                "muted",
            )
        )

        def apply_contact():
            self.set_sec_contact(contact.text())

        layout.addWidget(button("Use contact for this session", apply_contact, True))

        def clear_contact():
            self.set_sec_contact("")
            contact.clear()

        layout.addWidget(button("Clear session contact", clear_contact))
        self.content.addWidget(frame)
        frame, layout = card("Research score weights · sum must equal 100")
        weights = self.store.setting(
            "score_weights",
            {
                "technical": 25,
                "fundamentals": 25,
                "catalysts": 20,
                "options": 15,
                "political": 5,
                "reliability": 10,
            },
        )
        form = QFormLayout()
        inputs = {}
        for key, value in weights.items():
            spin = QSpinBox()
            spin.setRange(0, 100)
            spin.setValue(value)
            form.addRow(key.capitalize(), spin)
            inputs[key] = spin
        layout.addLayout(form)

        def save():
            proposed = {key: control.value() for key, control in inputs.items()}
            if sum(proposed.values()) != 100 or proposed.get("reliability", 0) == 0:
                self.error("Weights must total 100 and include a nonzero reliability weight")
                return
            self.store.set_setting("score_weights", proposed)
            self.status.setText("Research weights saved · evidence and quality abstention gates still apply")

        layout.addWidget(button("Save research weights", save, True))
        layout.addWidget(
            label(
                "Proposed priorities, not empirically fitted probabilities. Missing components earn no points and do not increase observed evidence. Custom weights cannot establish a validated trading strategy.",
                "muted",
            )
        )
        self.content.addWidget(frame)

    def backup(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Back up private local state",
            str(data_directory() / "techpulse-backup.db"),
            "SQLite (*.db)",
        )
        if path:
            try:
                self.store.backup(path)
                self.status.setText("Local backup created · " + path)
            except (ValueError, OSError, sqlite3.Error) as exc:
                self.error(str(exc))

    def restore_backup_dialog(self):
        from .recovery import RecoveryError, inspect_backup, restore_database

        if self.worker or self.recovery_busy:
            self.error("Wait for the current data operation to finish")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Inspect a TechPulse SQLite backup", "", "SQLite (*.db)")
        if not path:
            return
        self.recovery_busy = True
        self.scheduler.stop()
        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                summary = inspect_backup(path)
            finally:
                QApplication.restoreOverrideCursor()
            counts = summary["rows"]
            box = QMessageBox(self)
            box.setWindowTitle("Restore this backup?")
            box.setIcon(QMessageBox.Icon.Warning)
            box.setTextFormat(Qt.TextFormat.PlainText)
            box.setText(
                f"Validated backup: {counts['assets']} assets, {counts['bars']} price observations, {counts['paper']} paper transactions and {counts['reports']} reports.\n\nThis replaces both current workspaces and their settings. The current database will first be saved in its recovery folder. Close other TechPulse windows before continuing; edits made in another window after that safety copy are not protected.\n\nRestore the selected backup?"
            )
            box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
            box.setDefaultButton(QMessageBox.StandardButton.Cancel)
            if box.exec() != QMessageBox.StandardButton.Yes:
                self.status.setText("Restore cancelled; current data unchanged")
                return
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                result = restore_database(self.store, path)
            finally:
                QApplication.restoreOverrideCursor()
            self.last_recovery_point = result["recovery_point"]
            self.live_results = []
            self.sec_user_agent = ""
            seed_demo(self.store)
            self.theme = self.store.setting("theme", "dark")
            assets = self.store.assets(self.mode)
            self.active_symbol = assets[0]["symbol"] if assets else ""
            self.apply_theme()
            self.rebuild_page()
            self.status.setText(
                "Backup restored. Previous data saved at "
                + self.last_recovery_point
                + (" · " + result["warning"] if result.get("warning") else "")
            )
        except (RecoveryError, sqlite3.Error, OSError, ValueError) as exc:
            self.error(str(exc))
        finally:
            self.recovery_busy = False
            self.scheduler.start(60_000)

    def import_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Import authorized CSV into personal research")
        dialog.resize(640, 410)
        form = QFormLayout(dialog)
        kind = QComboBox()
        kind.addItems(["bars", "assets", "options", "contracts", "disclosures"])
        source, url = QLineEdit(), QLineEdit()
        source.setPlaceholderText("Original provider / filing / agency")
        url.setPlaceholderText("https://original-source.example/document")
        path = QLineEdit()
        browse = button(
            "Choose CSV…",
            lambda: path.setText(QFileDialog.getOpenFileName(dialog, "Select CSV", "", "CSV (*.csv)")[0]),
        )
        form.addRow("Record type", kind)
        form.addRow("Source name", source)
        form.addRow("Original source URL", url)
        form.addRow("CSV file", path)
        form.addRow(browse)
        check = QCheckBox("I have permission to use, retain and export these data locally")
        form.addRow(check)
        note = label(
            "All monetary fields require explicit currency=USD. Imports are all-or-nothing. See docs/IMPORT_FORMATS.md for schemas. Bars must be coherent positive OHLCV. Award/filing IDs update instead of double-counting. Do not import provider data whose terms prohibit this storage; SQLite is not encrypted. Political records require use-specific legal clearance.",
            "muted",
        )
        form.addRow(note)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Open | QDialogButtonBox.StandardButton.Cancel
        )
        form.addRow(buttons)
        buttons.rejected.connect(dialog.reject)

        def perform():
            if not check.isChecked():
                self.error("Confirm that your data use and local storage are authorized")
                return
            try:
                import_path = Path(path.text())
                if import_path.stat().st_size > 20_000_000:
                    raise ValueError("Import exceeds 20 MB")
                content = import_path.read_text(encoding="utf-8-sig")
                count = self.store.import_csv(content, kind.currentText(), source.text(), url.text())
            except (ValueError, OSError, UnicodeError) as exc:
                self.error(str(exc))
                return
            dialog.accept()
            self.workspace.setCurrentIndex(1)
            self.rebuild_page()
            self.status.setText(
                f"Imported {count} validated {kind.currentText()} row(s) into personal research"
            )

        buttons.accepted.connect(perform)
        dialog.exec()

    def show_record(self, title, record):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(900, 680)
        layout = QVBoxLayout(dialog)
        browser = QTextBrowser()
        browser.setPlainText(json.dumps(record, ensure_ascii=False, indent=2, default=str))
        layout.addWidget(browser)
        layout.addWidget(button("Close", dialog.accept))
        dialog.exec()

    def error(self, message):
        box = QMessageBox(self)
        box.setWindowTitle("TechPulse")
        box.setIcon(QMessageBox.Icon.Warning)
        box.setTextFormat(Qt.TextFormat.PlainText)
        box.setText(message)
        box.exec()

    def closeEvent(self, event):
        if self.worker or self.recovery_busy:
            self.status.setText("A data operation is finishing. Close again after it completes.")
            event.ignore()
            return
        self.closed = True
        self.scheduler.stop()
        self.store.close()
        event.accept()


def launch():
    from .startup import open_window

    existing = QApplication.instance()
    app = existing if isinstance(existing, QApplication) else QApplication([])
    app.setApplicationName("TechPulse")
    app.setOrganizationName("TechPulse")
    app.setFont(QFont("Segoe UI", 10))
    app.setQuitOnLastWindowClosed(False)
    window = open_window(MainWindow)
    if window is None:
        return 1
    window.show()
    app.setQuitOnLastWindowClosed(True)
    return app.exec()
