from __future__ import annotations

import html
import json
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QSettings, Qt, QThreadPool, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .adb import Adb, find_adb
from .demo import DemoEngine
from .downloads import download_adb
from .engine import Engine
from .models import DeviceInfo, Outcome, Plan
from .paths import data_dir

STYLE = """
QWidget { background:#0b111c; color:#dbe4f2; font-family:'Segoe UI','DejaVu Sans',sans-serif; font-size:13px; }
QMainWindow { background:#0b111c; }
QFrame#sidebar { background:#080d16; border-right:1px solid #202b3d; }
QLabel#brand { font-size:27px; font-weight:800; color:#ffffff; }
QLabel#eyebrow { color:#fa9a61; font-size:11px; font-weight:700; }
QLabel#title { font-size:28px; font-weight:700; color:#f2f6fd; }
QLabel#subtitle { color:#91a2ba; font-size:13px; }
QLabel#cardTitle { font-weight:600; font-size:15px; color:#edf3ff; }
QLabel#metric { font-size:29px; font-weight:700; color:#f0f6ff; }
QLabel#muted { color:#90a0b8; }
QLabel#status { background:#142b27; color:#78dfb1; border:1px solid #285344; padding:7px 13px; border-radius:12px; }
QFrame#card { background:#111b2b; border:1px solid #25334a; border-radius:13px; }
QFrame#card QLabel, QFrame#card QCheckBox { background:transparent; }
QPushButton { background:#19263a; color:#e5edf8; border:1px solid #30415d; border-radius:7px; padding:9px 14px; font-weight:600; }
QPushButton:hover { background:#22334e; border-color:#4c658b; }
QPushButton:disabled { color:#61718a; background:#111a29; border-color:#233047; }
QPushButton#primary { background:#f69458; color:#1b1210; border:0; font-weight:700; }
QPushButton#primary:hover { background:#ffad7b; }
QPushButton#nav { text-align:left; background:transparent; border:0; color:#8e9db5; padding:12px 14px; }
QPushButton#nav:checked { background:#202a3b; color:#ffb887; border-left:3px solid #f69458; border-radius:5px; }
QLineEdit, QComboBox { background:#0b1321; border:1px solid #30415a; border-radius:7px; padding:9px; }
QComboBox QAbstractItemView { background:#152135; selection-background-color:#2c4262; }
QCheckBox { spacing:10px; padding:5px 0; }
QCheckBox::indicator { width:17px; height:17px; border:1px solid #526580; border-radius:4px; background:#0d1726; }
QCheckBox::indicator:checked { background:#f69458; border-color:#ffb280; image:none; }
QCheckBox:disabled { color:#657690; }
QTableWidget, QListWidget, QTextEdit { background:#0e1827; border:1px solid #26364d; border-radius:8px; gridline-color:#243147; }
QTableWidget::item { padding:9px; border-bottom:1px solid #1d2b40; }
QTableWidget::item:selected, QListWidget::item:selected { background:#233955; }
QHeaderView::section { background:#152237; color:#94a8c5; padding:10px; border:0; font-size:11px; font-weight:600; }
QProgressBar { border:0; border-radius:3px; background:#1d2b41; max-height:5px; }
QProgressBar::chunk { background:#f69458; border-radius:3px; }
QScrollArea { border:0; }
QToolTip { background:#22334d; color:white; border:1px solid #506583; padding:5px; }
"""


class TaskSignals(QObject):
    result = Signal(object)
    error = Signal(str)
    log = Signal(str)


class Task(QRunnable):
    def __init__(self, function):
        super().__init__()
        self.function = function
        self.signals = TaskSignals()

    def run(self):
        try:
            self.signals.result.emit(self.function(self.signals.log.emit))
        except Exception as exc:
            self.signals.error.emit(str(exc))


def label(text: str, name: str = "", wrap: bool = True) -> QLabel:
    item = QLabel(text)
    if name:
        item.setObjectName(name)
    item.setWordWrap(wrap)
    item.setTextFormat(Qt.TextFormat.PlainText)
    return item


def card(title: str, description: str = "") -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(21, 18, 21, 18)
    layout.setSpacing(10)
    layout.addWidget(label(title, "cardTitle"))
    if description:
        layout.addWidget(label(description, "muted"))
    return frame, layout


class Window(QMainWindow):
    def __init__(self, demo: bool = False):
        super().__init__()
        self.demo = demo
        self.busy = False
        self.tasks: list[Task] = []
        self.info: DeviceInfo | None = None
        self.engine: Engine | DemoEngine | None = None
        self.package_data = []
        self.settings = QSettings("Firemod", "Firemod")
        stored = self.settings.value("adb", "")
        self.adb_path = str(stored) if stored and Path(str(stored)).is_file() else find_adb()
        self.pool = QThreadPool.globalInstance()
        self.setWindowTitle(f"Firemod {__version__}")
        self.resize(1190, 830)
        self.setMinimumSize(980, 720)
        self.setStyleSheet(STYLE)
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(220)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(22, 31, 22, 24)
        sl.addWidget(label("◈  Firemod", "brand"))
        sl.addWidget(label("MENO PESO. PIÙ FIRE TV.", "eyebrow"))
        sl.addSpacing(35)
        self.nav = []
        for index, title in enumerate(("01   Dispositivo", "02   Applicazioni", "03   Ottimizzazioni",
                                       "04   Ripristino", "05   Registro")):
            button = QPushButton(title)
            button.setObjectName("nav")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, i=index: self.navigate(i))
            sl.addWidget(button)
            self.nav.append(button)
        sl.addStretch()
        sl.addWidget(label("AGPL v3+ · Open source", "muted"))
        sl.addWidget(label(f"Versione {__version__}\nUSB e Wi-Fi · Nessun root", "muted"))
        root.addWidget(side)
        content = QWidget()
        outer = QVBoxLayout(content)
        outer.setContentsMargins(31, 28, 31, 22)
        outer.setSpacing(17)
        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.addWidget(label("IL TUO DISPOSITIVO, ALLEGGERITO", "eyebrow"))
        self.page_title = label("Una Fire TV, più leggera.", "title")
        heading.addWidget(self.page_title)
        heading.addWidget(label("Scegli cosa tenere. Applica le modifiche. Puoi tornare indietro.", "subtitle"))
        header.addLayout(heading, 1)
        self.badge = label("Non connesso", "status")
        header.addWidget(self.badge, 0, Qt.AlignmentFlag.AlignTop)
        outer.addLayout(header)
        self.pages = QStackedWidget()
        outer.addWidget(self.pages, 1)
        self.make_device_page()
        self.make_apps_page()
        self.make_options_page()
        self.make_restore_page()
        self.make_log_page()
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        outer.addWidget(self.progress)
        footer = QHBoxLayout()
        self.summary = label("Collega una Fire TV per iniziare.", "muted")
        footer.addWidget(self.summary, 1)
        self.apply_button = QPushButton("Rivedi le modifiche  →")
        self.apply_button.setObjectName("primary")
        self.apply_button.clicked.connect(self.review)
        footer.addWidget(self.apply_button)
        outer.addLayout(footer)
        root.addWidget(content, 1)
        self.navigate(0)
        self.update_controls()
        if demo:
            self.engine = DemoEngine()
            self.loaded((self.engine.inspect(), self.engine.packages(), True))
            self.badge.setText("DEMO · nessuna modifica")
        elif self.adb_path:
            self.scan()

    def make_device_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        connection, cl = card("Collega la Fire TV", "Abilita il debug ADB nelle opzioni sviluppatore e autorizza questo PC sulla TV.")
        row = QHBoxLayout()
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(220)
        self.device_combo.currentIndexChanged.connect(self.device_selection_changed)
        row.addWidget(self.device_combo, 1)
        self.scan_button = QPushButton("Rileva")
        self.scan_button.clicked.connect(self.scan)
        row.addWidget(self.scan_button)
        self.load_button = QPushButton("Apri dispositivo")
        self.load_button.clicked.connect(self.load_device)
        row.addWidget(self.load_button)
        cl.addLayout(row)
        row = QHBoxLayout()
        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("Indirizzo IP della Fire TV · es. 192.168.1.50")
        row.addWidget(self.ip_edit, 1)
        self.connect_button = QPushButton("Connetti Wi-Fi")
        self.connect_button.clicked.connect(self.connect_wifi)
        row.addWidget(self.connect_button)
        cl.addLayout(row)
        adb_row = QHBoxLayout()
        self.adb_label = label("ADB disponibile" if self.adb_path else "ADB non trovato", "muted")
        adb_row.addWidget(self.adb_label, 1)
        self.choose_adb = QPushButton("Scegli ADB…")
        self.choose_adb.clicked.connect(self.pick_adb)
        adb_row.addWidget(self.choose_adb)
        self.download_button = QPushButton("Installa ADB…")
        self.download_button.clicked.connect(self.setup_adb)
        adb_row.addWidget(self.download_button)
        cl.addLayout(adb_row)
        layout.addWidget(connection)
        metrics = QHBoxLayout()
        self.metric_values = []
        for title, sub in (("RAM disponibile", "Memoria disponibile, non RAM semplicemente in cache"),
                           ("Spazio libero", "Archiviazione interna /data"),
                           ("Home veloce", "Stato dell’acceleratore per questa accensione")):
            box, bl = card(title)
            value = label("—", "metric")
            self.metric_values.append(value)
            bl.addWidget(value)
            bl.addWidget(label(sub, "muted"))
            metrics.addWidget(box, 1)
        layout.addLayout(metrics)
        details, dl = card("Prima di cominciare")
        self.details_label = label("Rileva il dispositivo per verificarne modello, firmware e opzioni disponibili.", "muted")
        dl.addWidget(self.details_label)
        buttons = QHBoxLayout()
        self.preset_button = QPushButton("Prepara il profilo consigliato")
        self.preset_button.clicked.connect(self.recommended)
        buttons.addWidget(self.preset_button)
        self.refresh_button = QPushButton("Aggiorna diagnosi")
        self.refresh_button.clicked.connect(self.load_device)
        buttons.addWidget(self.refresh_button)
        dl.addLayout(buttons)
        layout.addWidget(details)
        layout.addStretch()
        self.pages.addWidget(page)

    def make_apps_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label("Seleziona le app da disattivare o riattivare. Dati e accessi vengono conservati.", "subtitle"))
        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Cerca nome o identificatore dell’app…")
        self.search.textChanged.connect(self.filter_apps)
        filters.addWidget(self.search, 1)
        self.show_system = QCheckBox("Mostra componenti protetti")
        self.show_system.toggled.connect(self.filter_apps)
        filters.addWidget(self.show_system)
        layout.addLayout(filters)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["MODIFICA", "APPLICAZIONE", "TIPO", "STATO"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for index, width in ((0, 90), (2, 110), (3, 150)):
            self.table.setColumnWidth(index, width)
        self.table.itemChanged.connect(self.update_summary)
        layout.addWidget(self.table, 1)
        layout.addWidget(label("I componenti essenziali sono bloccati. Se il firmware rifiuta una modifica, Firemod la segnala e la lascia invariata. Disattivare non libera lo spazio dell’APK.", "muted"))
        self.pages.addWidget(page)

    def make_options_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        self.animation_check = QCheckBox("Riduci le animazioni dell’interfaccia")
        self.animation_scale = QComboBox()
        for name, value in (("Nessuna animazione · massima reattività", "0"),
                            ("Durata delle animazioni dimezzata", "0.5"), ("Velocità standard", "1")):
            self.animation_scale.addItem(name, value)
        self.privacy_check = QCheckBox("Limita statistiche d’uso e tracciamento pubblicitario")
        self.screensaver_check = QCheckBox("Disattiva lo screensaver fotografico")
        self.home_check = QCheckBox("Installa Luncher e abilita Firemod Home")
        self.fast_check = QCheckBox("Attiva l’acceleratore della home per questa accensione")
        performance, pl = card("Più reattività", "Interventi mirati, con verifica delle impostazioni salvate.")
        pl.addWidget(self.animation_check)
        pl.addWidget(self.animation_scale)
        pl.addWidget(self.screensaver_check)
        layout.addWidget(performance)
        privacy, pp = card("Meno pubblicità e raccolta dati", "Le opzioni privacy limitano la raccolta dati. La home offline di Luncher elimina le inserzioni dalla schermata iniziale; le pubblicità dentro le app restano gestite dalle app.")
        pp.addWidget(self.privacy_check)
        layout.addWidget(privacy)
        home, hl = card("Una home essenziale", "La home Amazon viene conservata per le impostazioni e il ripristino. In questa versione l’integrazione è verificata su Fire OS 5 / Android 5.1.")
        hl.addWidget(self.home_check)
        hl.addWidget(self.fast_check)
        hl.addWidget(label("L’acceleratore continua a funzionare senza PC finché la Fire TV resta alimentata. Dopo un riavvio completo riattivalo da Firemod; nel frattempo funziona il metodo standard. Non riduce l’avvio di Android a zero.", "muted"))
        layout.addWidget(home)
        layout.addStretch()
        for check in (self.animation_check, self.privacy_check, self.screensaver_check,
                      self.home_check, self.fast_check):
            check.toggled.connect(self.update_summary)
        self.animation_scale.currentIndexChanged.connect(self.update_summary)
        self.pages.addWidget(page)

    def make_restore_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        box, bl = card("Punti di ripristino", "Salvati sul PC prima delle modifiche e associati al dispositivo selezionato. Tieni questa cartella se vuoi poter ripristinare le impostazioni.")
        self.history = QListWidget()
        bl.addWidget(self.history, 1)
        row = QHBoxLayout()
        self.restore_button = QPushButton("Ripristina il punto selezionato…")
        self.restore_button.clicked.connect(self.restore_selected)
        row.addWidget(self.restore_button)
        self.folder_button = QPushButton("Apri cartella locale")
        self.folder_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir()))))
        row.addWidget(self.folder_button)
        bl.addLayout(row)
        layout.addWidget(box, 1)
        self.pages.addWidget(page)

    def make_log_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label("Operazioni, verifiche e rifiuti del firmware. Il registro resta sul tuo PC.", "subtitle"))
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFont(QFont("monospace", 10))
        layout.addWidget(self.log_box, 1)
        self.pages.addWidget(page)

    def navigate(self, index: int):
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.nav):
            button.setChecked(i == index)
        titles = ("Una Fire TV, più leggera.", "Tieni ciò che usi.", "Scegli i miglioramenti.",
                  "Puoi tornare indietro.", "Tutto, alla luce del sole.")
        self.page_title.setText(titles[index])

    def task(self, function, result=None, mutation=False):
        if self.busy:
            return
        self.busy = True
        self.progress.setRange(0, 0)
        self.update_controls()
        task = Task(function)
        self.tasks.append(task)
        task.signals.log.connect(self.log)

        def finish(value=None, error=None):
            self.busy = False
            self.progress.setRange(0, 1)
            self.progress.setValue(0)
            if task in self.tasks:
                self.tasks.remove(task)
            self.update_controls()
            if error:
                self.log(error)
                QMessageBox.warning(self, "Operazione non completata", error)
                self.refresh_history()
            elif result:
                result(value)

        task.signals.result.connect(lambda value: finish(value=value))
        task.signals.error.connect(lambda message: finish(error=message))
        self.pool.start(task)

    def log(self, message: str):
        self.log_box.append(html.escape(message))
        self.summary.setText(message[:130])

    def update_controls(self):
        connected = self.engine is not None
        for item in (self.scan_button, self.load_button, self.connect_button, self.choose_adb,
                     self.download_button, self.device_combo, self.ip_edit):
            item.setEnabled(not self.busy and not self.demo)
        for item in (self.preset_button, self.refresh_button, self.table, self.animation_check,
                     self.animation_scale, self.privacy_check, self.screensaver_check, self.home_check,
                     self.fast_check, self.restore_button):
            item.setEnabled(connected and not self.busy)
        compatible = bool(self.info and self.info.sdk == 22 and self.info.is_fire_tv)
        self.home_check.setEnabled(compatible and not self.busy)
        self.fast_check.setEnabled(compatible and not self.busy)
        self.apply_button.setEnabled(connected and not self.busy and not self.demo)
        self.restore_button.setEnabled(connected and not self.busy and not self.demo)
        self.load_button.setEnabled(not self.busy and bool(self.adb_path) and not self.demo)
        self.connect_button.setEnabled(not self.busy and bool(self.adb_path) and not self.demo)

    def scan(self):
        if not self.adb_path:
            self.log("Scegli ADB o installa gli Android Platform-Tools.")
            return
        path = self.adb_path

        def show(devices):
            selected = self.device_combo.currentData()
            self.device_combo.clear()
            for device in devices:
                name = f"{device.model or device.serial} · {device.state}"
                self.device_combo.addItem(name, device.serial)
                self.device_combo.setItemData(self.device_combo.count() - 1, device.state, Qt.ItemDataRole.UserRole + 1)
            if selected:
                index = self.device_combo.findData(selected)
                if index >= 0:
                    self.device_combo.setCurrentIndex(index)
            self.log(f"Dispositivi rilevati: {len(devices)}. Autorizza il PC sulla TV se appare 'unauthorized'.")

        self.task(lambda log: Adb(path).devices(), show)

    def connect_wifi(self):
        address, path = self.ip_edit.text(), self.adb_path
        if not address.strip() or not path:
            return
        self.task(lambda log: Adb(path).connect(address), lambda value: (self.log(value), self.scan()))

    def pick_adb(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleziona adb.exe o adb")
        if path:
            self.set_adb(path)

    def set_adb(self, path):
        self.adb_path = path
        self.settings.setValue("adb", path)
        self.adb_label.setText("ADB disponibile")
        self.scan()

    def setup_adb(self):
        box = QMessageBox(self)
        box.setWindowTitle("Android Platform-Tools")
        box.setText("Scarica ADB dal sito ufficiale Google")
        box.setInformativeText("Il download avviene da dl.google.com e viene salvato nella cartella locale di Firemod. I Platform-Tools sono distribuiti secondo i termini SDK di Google: developer.android.com/studio/terms.")
        box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        box.button(QMessageBox.StandardButton.Ok).setText("Accetta i termini e scarica")
        if box.exec() == QMessageBox.StandardButton.Ok:
            self.task(lambda log: download_adb(log), self.set_adb)

    def load_device(self):
        if self.demo:
            return
        serial, path = self.device_combo.currentData(), self.adb_path
        if not serial or not path:
            self.log("Seleziona un dispositivo autorizzato.")
            return
        state = self.device_combo.currentData(Qt.ItemDataRole.UserRole + 1)
        if state != "device":
            self.log("Autorizza il debug sullo schermo della Fire TV, poi premi Rileva.")
            return
        engine = Engine(Adb(path, serial))

        def inspect(log):
            log("Lettura di modello, firmware e applicazioni…")
            info = engine.require_fire_tv()
            return info, engine.packages(), engine.bridge_status()

        def loaded(value):
            self.engine = engine
            self.loaded(value)

        self.task(inspect, loaded)

    def device_selection_changed(self, index):
        if isinstance(self.engine, Engine) and self.device_combo.currentData() != self.engine.adb.serial:
            self.engine = None
            self.info = None
            self.package_data = []
            self.table.setRowCount(0)
            self.history.clear()
            self.badge.setText("Apri il dispositivo")
            self.update_controls()

    def loaded(self, value):
        self.info, self.package_data, fast = value
        if self.info.sdk != 22:
            self.home_check.setChecked(False)
            self.fast_check.setChecked(False)
        self.badge.setText(f"●  {self.info.model} connessa")
        self.metric_values[0].setText(f"{self.info.available_mb} MB")
        self.metric_values[1].setText(self.info.free_storage)
        self.metric_values[2].setText("Attiva" if fast else "Standard")
        compatibility = ("Home leggera e acceleratore disponibili." if self.info.sdk == 22
                         else "Gestione app e impostazioni disponibili. Integrazione Home limitata a Fire OS 5.")
        self.details_label.setText(f"{self.info.model} · {self.info.fire_os or 'Fire OS'} · Android {self.info.android}\n"
                                   f"RAM di sistema: {self.info.total_mb} MB · App disattivate: {self.info.disabled_count}\n"
                                   + compatibility)
        self.populate_apps()
        self.refresh_history()
        self.update_controls()
        self.update_summary()

    def populate_apps(self):
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.package_data))
        for row, package in enumerate(self.package_data):
            check = QTableWidgetItem()
            check.setData(Qt.ItemDataRole.UserRole, package.name)
            inactive = package.disabled or package.hidden
            if not package.protected:
                check.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
                check.setCheckState(Qt.CheckState.Unchecked)
            else:
                check.setFlags(Qt.ItemFlag.NoItemFlags)
            self.table.setItem(row, 0, check)
            name = QTableWidgetItem(package.label + "\n" + package.name)
            name.setToolTip(package.note or package.name)
            self.table.setItem(row, 1, name)
            self.table.setItem(row, 2, QTableWidgetItem("Sistema" if package.system else "App"))
            status = "Protetta" if package.protected else "Inattiva · riattivabile" if inactive else "Attiva"
            state = QTableWidgetItem(status)
            state.setForeground(QColor("#7a90ad" if package.protected else "#7bdbad"))
            self.table.setItem(row, 3, state)
            self.table.setRowHeight(row, 61)
        self.table.blockSignals(False)
        self.filter_apps()

    def filter_apps(self):
        query = self.search.text().casefold()
        for row, package in enumerate(self.package_data):
            match = query in (package.name + " " + package.label).casefold()
            self.table.setRowHidden(row, not match or (package.protected and not self.show_system.isChecked()))

    def selected_packages(self):
        return [self.table.item(row, 0).data(Qt.ItemDataRole.UserRole) for row in range(self.table.rowCount())
                if self.table.item(row, 0).checkState() == Qt.CheckState.Checked]

    def plan(self):
        selected = set(self.selected_packages())
        disable = [p.name for p in self.package_data if p.name in selected and not (p.hidden or p.disabled)]
        enable = [p.name for p in self.package_data if p.name in selected and (p.hidden or p.disabled)]
        return Plan(self.animation_scale.currentData() if self.animation_check.isChecked() else None,
                    self.privacy_check.isChecked(), self.screensaver_check.isChecked(),
                    self.home_check.isChecked(), self.fast_check.isChecked(), disable, enable)

    def update_summary(self, *args):
        if not hasattr(self, "summary"):
            return
        plan = self.plan()
        options = sum((plan.animations is not None, plan.privacy, plan.screensaver, plan.launcher, plan.accelerator))
        self.summary.setText(f"{len(plan.packages)} app da disattivare · {len(plan.enable_packages)} da riattivare · {options} ottimizzazioni")

    def recommended(self):
        self.animation_check.setChecked(True)
        self.animation_scale.setCurrentIndex(0)
        self.privacy_check.setChecked(True)
        self.home_check.setChecked(bool(self.info and self.info.sdk == 22))
        self.fast_check.setChecked(bool(self.info and self.info.sdk == 22))
        self.navigate(2)

    def review(self):
        if not isinstance(self.engine, Engine):
            return
        plan = self.plan()
        if plan.empty:
            self.navigate(2)
            self.log("Seleziona almeno una modifica.")
            return
        lines = []
        if plan.animations is not None:
            lines.append("Animazioni: " + plan.animations)
        if plan.privacy:
            lines.append("Limita raccolta dati e tracciamento")
        if plan.screensaver:
            lines.append("Disattiva screensaver fotografico")
        if plan.launcher:
            lines.append("Installa Luncher e Firemod Home")
        if plan.accelerator:
            lines.append("Acceleratore Home fino al prossimo riavvio")
        lines.extend("Disattiva: " + name for name in plan.packages)
        lines.extend("Riattiva: " + name for name in plan.enable_packages)
        box = QMessageBox(self)
        box.setWindowTitle("Modifiche da applicare")
        box.setText(f"Applica a {self.info.model}?")
        box.setInformativeText("\n".join(lines) + "\n\nPrima delle modifiche verrà salvato un punto di ripristino locale.")
        box.setStandardButtons(QMessageBox.StandardButton.Apply | QMessageBox.StandardButton.Cancel)
        box.setDefaultButton(QMessageBox.StandardButton.Cancel)
        if box.exec() != QMessageBox.StandardButton.Apply:
            return
        engine = self.engine

        def execute(log):
            engine.log = log
            return engine.apply(plan)

        self.navigate(4)
        self.task(execute, self.completed, mutation=True)

    def completed(self, outcome: Outcome):
        for prefix, values in (("OK", outcome.done), ("INVARIATO", outcome.skipped), ("ERRORE", outcome.errors)):
            for message in values:
                self.log(f"[{prefix}] {message}")
        self.refresh_history()
        QMessageBox.information(self, "Operazione terminata",
                                f"Operazioni completate: {len(outcome.done)}\n"
                                f"Invariate o non consentite: {len(outcome.skipped)}\n"
                                f"Errori: {len(outcome.errors)}\n\nIl dettaglio è nel registro e nel punto di ripristino.")
        self.load_device()

    def refresh_history(self):
        self.history.clear()
        if self.engine:
            for path in self.engine.snapshots():
                try:
                    record = json.loads(path.read_text(encoding="utf-8"))
                    count = len(record.get("operations", []))
                    item = QListWidgetItem(f"{record['created'][:19].replace('T', ' ')} UTC   ·   {count} operazioni")
                    item.setData(Qt.ItemDataRole.UserRole, str(path))
                    self.history.addItem(item)
                except (OSError, KeyError, ValueError):
                    continue

    def restore_selected(self):
        item = self.history.currentItem()
        if not item or not isinstance(self.engine, Engine):
            return
        if QMessageBox.question(self, "Ripristino", "Ripristinare le impostazioni salvate in questo punto? Le modifiche successive agli stessi valori saranno sostituite.") != QMessageBox.StandardButton.Yes:
            return
        engine = self.engine
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        self.navigate(4)
        self.task(lambda log: engine.restore(path), self.completed, mutation=True)

    def closeEvent(self, event):
        if self.busy:
            self.summary.setText("Attendi la conclusione dell’operazione prima di chiudere Firemod.")
            event.ignore()
        else:
            event.accept()
