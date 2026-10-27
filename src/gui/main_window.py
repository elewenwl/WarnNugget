import sys
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QCoreApplication

try:
    from shiboken6 import isValid as _shiboken_is_valid
except Exception:
    _shiboken_is_valid = lambda _obj: True


def _still_running(worker) -> bool:
    if worker is None:
        return False
    try:
        if not _shiboken_is_valid(worker):
            return False
        return worker.isRunning()
    except RuntimeError:
        return False

from src.qt.mainwindow_ui import Ui_Nugget
import src.gui.pages as Pages

from src.controllers.translator import Translator
from src.controllers.preset_manager import PresetManager

from src.gui.pages.pages_list import Page

if TYPE_CHECKING:
    from src.devicemanagement.device_manager import DeviceManager

from src.gui.ios.theme_manager import ThemeManager
from src.gui.ios.home import IOSHomePage
from src.gui.ios.tweaks import IOSTweaksPage, IOSSectionPage
from src.gui.ios.posterboard import IOSPosterboardPage
from src.gui.ios.templates import IOSTemplatesPage
from src.gui.ios.daemons import IOSDaemonsPage
from src.gui.ios.apply import IOSApplyPage
from src.gui.ios.settings import IOSSettingsPage
from src.gui.ios.presets import IOSPresetsPage
from src.gui.ios.catalog import IOSCatalogPage
from src.gui.ios.statusbar import IOSStatusBarPage
from src.gui.ios.icon_themes import IOSIconThemesPage
from src.gui.ios.passcode_theme import IOSPasscodeThemePage
from src.gui.ios.connect_placeholder import ConnectDevicePlaceholder
from src.gui.thread_workers.apply_worker import DeviceMonitorThread
from src.tweaks.registry import Section

from src.gui.theme import ColorThemeManager, t, theme_icon, themed_stylesheet

from src.gui.main_window_mixins import (
    ApplyMixin,
    DeviceBarMixin,
    NavigationMixin,
    SettingsMixin,
)

_CLASSIC_THEMED_ICONS = {
    "phoneIconBtn": ":/icon/phone.svg",
    "refreshBtn": ":/icon/arrow-clockwise.svg",
    "homePageBtn": ":/icon/house.svg",
    "gestaltPageBtn": ":/icon/iphone-island.svg",
    "euEnablerPageBtn": ":/icon/geo-alt.svg",
    "statusBarPageBtn": ":/icon/features/status-bar.png",
    "passcodePageBtn": ":/icon/features/passcode-theme.png",
    "springboardOptionsPageBtn": ":/icon/app-indicator.svg",
    "internalOptionsPageBtn": ":/icon/hdd.svg",
    "liquidGlassPageBtn": ":/icon/liquid-glass.svg",
    "daemonsPageBtn": ":/icon/features/daemons.png",
    "iconThemesPageBtn": ":/icon/features/icon-themes.png",
    "presetsPageBtn": ":/icon/folder.svg",
    "applyPageBtn": ":/icon/check-circle.svg",
    "posterboardPageBtn": ":/icon/features/posterboard.png",
    "templatesPageBtn": ":/icon/file-earmark-text.svg",
    "settingsPageBtn": ":/icon/gear.svg",
    "mainDevBtn": ":/icon/github.svg",
    "discordBtn": ":/icon/discord.svg",
    "starOnGithubBtn": ":/icon/star.svg",
    "leminGithubBtn": ":/icon/github.svg",
    "leminTwitterBtn": ":/icon/twitter.svg",
    "leminKoFiBtn": ":/icon/currency-dollar.svg",
}

_CLASSIC_BORDERED_BTNS = [
    "helpFromBtn", "posterRestoreBtn", "snoolieBtn", "disfordottieBtn",
    "mikasaBtn", "wind0ws11AeroBtn", "translatorsBtn", "libiBtn",
    "duyBtn", "jjtechBtn", "qtBtn",
]

class MainWindow(QtWidgets.QMainWindow, DeviceBarMixin, SettingsMixin,
                 NavigationMixin, ApplyMixin):
    IOS_CONTENT_MAX_WIDTH = 1200

    def __init__(self, device_manager: "DeviceManager", translator: Translator):
        super(MainWindow, self).__init__()
        self.device_manager = device_manager
        self.translator = translator
        self.settings = self.translator.settings
        self.ui = Ui_Nugget()
        self.ui.setupUi(self)
        
        self.setWindowTitle("WarNugget")
        
        from src.gui.widgets import NavigationSidebar
        self.ui.sidebar.hide()
        self.ui.sidebar = NavigationSidebar(self.ui, self)
        self.setMaximumSize(16777215, 16777215)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                           QtWidgets.QSizePolicy.Preferred)
        self.noneText = self.tr("None")
        self.apply_in_progress = False
        self.refresh_in_progress = False
        self._device_change_refresh_pending = False
        self._device_refresh_timer = QtCore.QTimer(self)
        self._device_refresh_timer.setSingleShot(True)
        self._device_refresh_timer.timeout.connect(self._refresh_after_device_event)
        self.device_scan_completed = False
        self._cache_restore_in_progress = False
        self._cache_restore_thread = None

        self.preset_manager = PresetManager()
        self._preset_autosave_pending = False

        self.loadSettings()
        self._load_last_preset()
        self._register_tweak_autosave()

        self.initial_load = True

        self.ui.posterboardPageBtn.hide()
        self.ui.euEnablerPageBtn.hide()
        self.ui.statusBarPageBtn.hide()
        self.ui.springboardOptionsPageBtn.hide()
        self.ui.internalOptionsPageBtn.hide()
        self.ui.liquidGlassPageBtn.hide()
        self.ui.daemonsPageBtn.hide()
        self.ui.iconThemesPageBtn.hide()
        self.ui.passcodePageBtn.hide()
        self.ui.applyPageBtn.hide()
        self.ui.sidebarDiv1.hide()
        self.ui.sidebarDiv2.hide()

        self.pages = {
            Page.Home: Pages.Home(window=self, ui=self.ui),
            Page.Daemons: Pages.Daemons(ui=self.ui, window=self)
        }

        self.theme_manager = ThemeManager(self)

        self._color_theme = ColorThemeManager.instance()
        self._color_theme.theme_changed.connect(self._on_color_theme_changed)

        self.ios_pages = QtWidgets.QStackedWidget(self)
        self.ios_pages.setStyleSheet(t("page_bg"))
        self.ios_home = IOSHomePage(self)
        self.ios_tweaks = IOSTweaksPage(self)
        self.ios_posterboard = IOSPosterboardPage(self)
        self.ios_daemons = IOSDaemonsPage(self)
        self.ios_settings = IOSSettingsPage(self)
        self.ios_presets = IOSPresetsPage(self)
        self.ios_statusbar = IOSStatusBarPage(self)
        self.ios_apply = IOSApplyPage(self)
        self.ios_springboard = IOSSectionPage(self, Section.SPRINGBOARD)
        self.ios_internal = IOSSectionPage(self, Section.INTERNAL)
        self.ios_liquidglass = IOSSectionPage(self, Section.LIQUID_GLASS)
        self.ios_iconthemes = IOSIconThemesPage(self)
        self.ios_passthemes = IOSPasscodeThemePage(self)
        self.ios_catalog = IOSCatalogPage(self)
        self.ios_templates = IOSTemplatesPage(self)
        self.ios_pages.addWidget(self.ios_home)
        self.ios_pages.addWidget(self.ios_tweaks)
        self.ios_pages.addWidget(self.ios_posterboard)
        self.ios_pages.addWidget(self.ios_daemons)
        self.ios_pages.addWidget(self.ios_settings)
        self.ios_pages.addWidget(self.ios_statusbar)
        self.ios_pages.addWidget(self.ios_apply)
        self.ios_pages.addWidget(self.ios_springboard)
        self.ios_pages.addWidget(self.ios_internal)
        self.ios_pages.addWidget(self.ios_liquidglass)
        self.ios_pages.addWidget(self.ios_iconthemes)
        self.ios_pages.addWidget(self.ios_passthemes)
        self.ios_pages.addWidget(self.ios_presets)
        self.ios_pages.addWidget(self.ios_catalog)
        self.ios_pages.addWidget(self.ios_templates)

        from src.gui.widgets import IOSNavBar
        self.ios_nav = IOSNavBar("", on_back=self._go_back)
        self._ios_page_titles = {
            0: "WarNugget",
            1: QtCore.QCoreApplication.translate("Nugget", "Tweaks"),
            2: "PosterBoard",
            3: QtCore.QCoreApplication.translate("Nugget", "Daemons"),
            4: QtCore.QCoreApplication.translate("Nugget", "Settings"),
            5: QCoreApplication.translate("Nugget", "Status Bar"),
            6: QCoreApplication.translate("Nugget", "Apply"),
            7: QtCore.QCoreApplication.translate("Nugget", "SpringBoard"),
            8: QtCore.QCoreApplication.translate("Nugget", "Internal"),
            9: QtCore.QCoreApplication.translate("Nugget", "Liquid Glass"),
            10: QtCore.QCoreApplication.translate("Nugget", "Icon Themes"),
            11: QCoreApplication.translate("Nugget", "Passcode Theme"),
            12: QCoreApplication.translate("Nugget", "Presets"),
            13: QCoreApplication.translate("Nugget", "Community Catalog"),
            14: QCoreApplication.translate("Nugget", "Templates"),
        }
        self._nav_right_actions = {
            2: (QCoreApplication.translate("Nugget", "+ Add Tendies"), self.ios_posterboard.show_add_tendies_dialog),
            14: (QCoreApplication.translate("Nugget", "+ Import Templates"), self.ios_templates.show_add_templates_dialog),
            11: (QCoreApplication.translate("Nugget", "+ Theme"),
                 self.ios_passthemes.choose_theme_dialog),
        }
        self.ios_pages.currentChanged.connect(self._update_shared_nav)

        ios_root = QtWidgets.QWidget(self)
        ios_root_hbox = QtWidgets.QHBoxLayout(ios_root)
        ios_root_hbox.setContentsMargins(0, 0, 0, 0)
        ios_root_hbox.setSpacing(0)
        ios_column = QtWidgets.QWidget(ios_root)
        ios_column.setMaximumWidth(self.IOS_CONTENT_MAX_WIDTH)
        ios_root_hbox.addStretch(0)
        ios_root_hbox.addWidget(ios_column, 1)
        ios_root_hbox.addStretch(0)
        ios_root_layout = QtWidgets.QVBoxLayout(ios_column)
        ios_root_layout.setContentsMargins(0, 0, 0, 0)
        ios_root_layout.setSpacing(0)
        nav_wrap = QtWidgets.QWidget(ios_column)
        nav_wrap.setObjectName("iosNavWrap")
        nav_wrap_layout = QtWidgets.QVBoxLayout(nav_wrap)
        nav_wrap_layout.setContentsMargins(8, 8, 8, 0)
        nav_wrap_layout.setSpacing(0)
        nav_wrap_layout.addWidget(self.ios_nav)
        ios_root_layout.addWidget(nav_wrap)
        ios_root_layout.addWidget(self.ios_pages, 1)
        from src.gui.liquid.dock import LiquidDock as BottomNavigation
        self.bottom_navigation = BottomNavigation(self, ios_root)

        self._classic_parking = QtWidgets.QWidget(self)
        self._classic_parking.hide()
        self.ui.centralwidget.setParent(self._classic_parking)
        self.ui.homePage.setParent(None)
        self.ui.sidebar.setParent(None)
        self.ui.daemonsPage.setParent(None)
        self.ui.deviceBar.setParent(None)
        self.content_stack = QtWidgets.QStackedWidget(self)
        self.content_stack.addWidget(self.ui.homePage)
        self.content_stack.addWidget(ios_root)
        self.content_stack.addWidget(self.ui.daemonsPage)
        self.connect_placeholder = ConnectDevicePlaceholder(self)
        self.content_stack.addWidget(self.connect_placeholder)
        shell = QtWidgets.QWidget(self)
        shell.setProperty("cls", "central")
        self.shell_layout = QtWidgets.QVBoxLayout(shell)
        self.shell_layout.setContentsMargins(0, 0, 0, 0)
        self.shell_layout.setSpacing(0)
        self.shell_layout.addWidget(self.ui.deviceBar)
        self.body_row = QtWidgets.QHBoxLayout()
        self.body_row.setContentsMargins(0, 0, 0, 0)
        self.body_row.setSpacing(0)
        self.body_row.addWidget(self.ui.sidebar)
        self.body_row.addWidget(self.content_stack, 1)
        self.shell_layout.addLayout(self.body_row)
        self.setCentralWidget(shell)

        self.apply_theme(self.theme_manager.current_theme)
        QtWidgets.QApplication.instance().installEventFilter(self)

        self.updateAppVersionLabel()
        self.pages[Page.Home].load()
        
        self.ui.refreshBtn.clicked.connect(self.refresh_devices)
        self.ui.refreshBtn.setToolTip(QCoreApplication.translate("Nugget", "Refresh connected devices"))
        self.ui.devicePicker.currentIndexChanged.connect(self.change_selected_device)
        self._device_monitor_thread = DeviceMonitorThread(self)
        self._device_monitor_thread.devices_changed.connect(self._on_device_connection_changed)
        self._device_monitor_thread.usb_devices_changed.connect(self._on_usb_devices_changed)
        self._device_monitor_thread.start()
        self.refresh_devices()
        self._update_device_gate()

        self.ui.homePageBtn.clicked.connect(self.on_homePageBtn_clicked)
        self.ui.statusBarPageBtn.clicked.connect(self.on_statusBarPageBtn_clicked)
        self.ui.springboardOptionsPageBtn.clicked.connect(self.on_springboardOptionsPageBtn_clicked)
        self.ui.internalOptionsPageBtn.clicked.connect(self.on_internalOptionsPageBtn_clicked)
        self.ui.liquidGlassPageBtn.clicked.connect(self.on_liquidGlassPageBtn_clicked)
        self.ui.daemonsPageBtn.clicked.connect(self.on_daemonsPageBtn_clicked)
        self.ui.iconThemesPageBtn.clicked.connect(self.on_iconThemesPageBtn_clicked)
        self.ui.posterboardPageBtn.clicked.connect(self.on_posterboardPageBtn_clicked)
        self.ui.templatesPageBtn.clicked.connect(self.on_templatesPageBtn_clicked)
        self.ui.applyPageBtn.clicked.connect(self.on_applyPageBtn_clicked)
        self.ui.settingsPageBtn.clicked.connect(self.on_settingsPageBtn_clicked)

        self.ui.presetsPageBtn.clicked.connect(self.on_presetsPageBtn_clicked)

        self._apply_global_stylesheet()
        from src.gui.liquid.experience import LiquidExperience
        self.liquid = LiquidExperience(self)
        QtCore.QTimer.singleShot(0, self._prewarm_control_pages)

        self._warning_shown = False
        self._warning_timer = QtCore.QTimer(self)
        self._warning_timer.timeout.connect(self._check_for_warning)
        self._warning_timer.start(1000)

    def _check_for_warning(self):
        if self._warning_shown:
            return
            
        if self.device_manager.devices:
            self._warning_shown = True
            self._warning_timer.stop()
            
            box = QtWidgets.QMessageBox(self)
            box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            box.setWindowTitle("WarNugget Warning")
            box.setText("ВНИМАНИЕ! Обнаружено подключение iPhone.")
            box.setInformativeText(
                "Установка обоев (PosterBoard) на iOS 27 может привести к потере данных или циклической перезагрузке.\n\n"
                "Вы делаете это на свой страх и риск."
            )
            box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
            box.exec()

    def _prewarm_control_pages(self):
        self.ios_tweaks.prepare_content(finish=False)
        self.ios_daemons.prepare_content(finish=False)

    def run_first_launch_prompts(self):
        if not self.settings.value("ui/interface_choice_done", False, type=bool):
            from src.gui.interface_picker import InterfacePickerDialog
            picker = InterfacePickerDialog(self)
            picker.exec()
            if picker.choice is not None:
                show_sidebar = picker.choice == "classic"
                self.set_sidebar_enabled(show_sidebar)
                switch = self.ios_settings.sidebar_switch
                with QtCore.QSignalBlocker(switch):
                    switch.setChecked(show_sidebar)
                self.settings.setValue("ui/interface_choice_done", True)
                self._sync_settings()

        if not self.settings.value("backup_prompt_done", False, type=bool):
            if self.prompt_first_launch_backup():
                self.settings.setValue("backup_prompt_done", True)
                self._sync_settings()

        if "--test-mode" not in sys.argv:
            from src.gui.dialogs.linux_deps_dialog import prompt_and_install, should_prompt_on_startup
            if should_prompt_on_startup(self):
                prompt_and_install(self, from_startup=True)

    def _apply_global_stylesheet(self):
        self.setStyleSheet(t("global"))
        self._applied_color_mode = self._color_theme.mode
        self._color_theme.apply_to_app()
        self.ios_pages.setStyleSheet(t("page_bg"))
        if self.theme_manager.current_theme == ThemeManager.CLASSIC:
            self._retheme_classic()

    def _retheme_classic(self):
        c = self._color_theme.colors
        for obj_name, res in _CLASSIC_THEMED_ICONS.items():
            widget = getattr(self.ui, obj_name, None)
            if widget is not None:
                widget.setIcon(theme_icon(res, c.text_primary))

        self.ui.phoneNameLbl.setStyleSheet(f"color: {c.text_primary};")
        self.ui.phoneVersionLbl.setText(
            f'<a style="text-decoration:none; color:{c.text_secondary}" href="#">Version</a>')

        self.ui.sidebar._retheme()

        bordered_style = themed_stylesheet("classic_bordered_btn")
        for obj_name in _CLASSIC_BORDERED_BTNS:
            widget = getattr(self.ui, obj_name, None)
            if widget is not None:
                widget.setStyleSheet(bordered_style)

    def _on_color_theme_changed(self):
        if self.theme_manager.current_theme == ThemeManager.CLASSIC:
            self._apply_global_stylesheet()
            return
        if getattr(self, '_applied_color_mode', None) != self._color_theme.mode:
            self._apply_global_stylesheet()
        page = self.ios_pages.currentWidget()
        if page is not None and hasattr(page, "_retheme"):
            page._retheme()
            page._applied_theme_revision = self._color_theme.revision

    def closeEvent(self, event):
        terminating = []
        if getattr(self, "apply_in_progress", False):
            terminating.append(QCoreApplication.translate("Nugget", "apply/reset"))
        if getattr(self, "_cache_restore_in_progress", False):
            terminating.append(QCoreApplication.translate("Nugget", "data restore"))
        pt_worker = getattr(getattr(self, "ios_passthemes", None), "_worker", None)
        if _still_running(pt_worker):
            terminating.append(QCoreApplication.translate("Nugget", "passcode theme write"))
        pairing_worker = getattr(
            getattr(self, "ios_settings", None), "_reset_pairing_thread", None)
        if _still_running(pairing_worker):
            terminating.append(QCoreApplication.translate("Nugget", "pairing reset"))
        if terminating:
            reply = QtWidgets.QMessageBox.question(
                self,
                QCoreApplication.tr("Background device operation"),
                QCoreApplication.translate(
                    "Nugget",
                    "A device %1 is running. Closing now can interrupt it "
                    "mid-write and leave the protective backup corrupted.\n\n"
                    "Close anyway?").replace(
                        "%1", " and ".join(terminating)),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.StandardButton.Cancel,
            )
            if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            for worker in (
                getattr(self, "worker_thread", None),
                getattr(self, "_cache_restore_thread", None),
                pairing_worker,
                pt_worker,
            ):
                if _still_running(worker):
                    try:
                        worker.wait()
                    except RuntimeError:
                        pass
        self._device_selection_closing = True
        self._posterboard_waiting = {}
        for worker in list(getattr(self, "_posterboard_selection_workers", {}).values()):
            if _still_running(worker) and not worker.wait(2000):
                event.ignore()
                return
        if not self.ios_home.stop_device_info():
            event.ignore()
            return
        if not self.ios_home._device_preview.stop() or not self.ios_home._picker_preview.stop():
            event.ignore()
            return
        scan_worker = getattr(self, "refresh_worker_thread", None)
        if _still_running(scan_worker):
            try:
                scan_worker.wait(8000)
            except RuntimeError:
                pass
        monitor_worker = getattr(self, "_device_monitor_thread", None)
        if _still_running(monitor_worker):
            monitor_worker.request_stop()
            try:
                monitor_worker.wait(10000)
            except RuntimeError:
                pass
        self._flush_autosave()
        super().closeEvent(event)