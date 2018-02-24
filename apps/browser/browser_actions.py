
from PyQt5.QtCore import pyqtSlot, QDir
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from browser_window import Browser


class MainWindow(QMainWindow, Browser):
    """
    Class documentation goes here.
    """

    def __init__(self, parent=None, **kwargs):
        super(MainWindow, self).__init__(parent)
        self.browser = Browser
        self.initBUI(self)

    @pyqtSlot()
    def on_actionExit_triggered(self):
        """
        This Slot is executed when a exit signal was fire. The application is
        terminate
        """
        import sys
        sys.exit()

    def _onPathDoubleClick(self, signal):
        """
        This slot is executed when the action "double click"  inside the tree
        view is realized. The tree view path change
        :param signal: double clicked signal
        """
        file_path = self.model.filePath(signal)
        self.browser.setLineCompleter(self, file_path)


    def _onPathClick(self, signal):
        """
        This slot is executed when the action "click" inside the tree view
        is realized. The tree view path change
        :param signal: clicked signal
        """
        file_path = self.model.filePath(signal)
        self.browser.setLineCompleter(self, file_path)
        self.browser.imagePlot(self, file_path)

