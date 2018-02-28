from os.path import dirname
import sys
from PyQt5.QtWidgets import QApplication

# Add the path to the library, go 3 levels up
sys.path.append(dirname(dirname(dirname(__file__))))

from window import MainWindow

    
if __name__ == "__main__":
    app = QApplication(sys.argv)

    kwargs = {}
    if len(sys.argv) > 1:
        kwargs['imageFile'] = sys.argv[1]

    mWindow = MainWindow(**kwargs)
    mWindow.show()
    sys.exit(app.exec_())
