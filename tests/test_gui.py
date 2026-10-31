import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QThread, QTimer
from PySide6.QtWidgets import QApplication

from firemod.gui import Window


def test_demo_is_read_only_and_recommended_profile_never_selects_apps():
    app = QApplication.instance() or QApplication([])
    window = Window(demo=True)
    assert window.info.model == "AFTT"
    assert not window.apply_button.isEnabled()
    window.recommended()
    plan = window.plan()
    assert plan.animations == "0"
    assert plan.privacy and plan.launcher and plan.accelerator
    assert plan.packages == []
    assert not window.apply_button.isEnabled()
    window.close()
    app.processEvents()


def test_worker_result_is_delivered_on_the_gui_thread():
    app = QApplication.instance() or QApplication([])
    window = Window(demo=True)
    loop = QEventLoop()
    results = []

    def receive(value):
        results.append((value, QThread.currentThread() == app.thread()))
        loop.quit()

    window.task(lambda log: "finished", receive)
    QTimer.singleShot(3000, loop.quit)
    loop.exec()
    assert results == [("finished", True)]
    assert not window.busy
    window.close()
