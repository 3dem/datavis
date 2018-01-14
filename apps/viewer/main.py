from PyQt5.QtWidgets import QApplication

from window import MainWindow

    
if __name__ == "__main__":
    import sys
       
    app = QApplication(sys.argv)

    kwargs = {}
    if len(sys.argv) > 1:
        kwargs['imageFile'] = sys.argv[1]

    mWindow = MainWindow(**kwargs)
    mWindow.show()
    sys.exit(app.exec_())
