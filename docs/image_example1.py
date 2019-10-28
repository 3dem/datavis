import sys
import PyQt5.QtWidgets as qtw
import datavis as dv
import emvis as emv

# Read the input filename from first argument
imgPath = sys.argv[1]
app = qtw.QApplication(sys.argv)
win = qtw.QMainWindow()
# Create the image model and view
data = emv.ImageManager().getData(imgPath)
imgModel = dv.models.ImageModel(data=data)
imgView = dv.views.ImageView(model=imgModel, parent=win,
                             histogram=True)  # show histogram of pixel values
win.setCentralWidget(imgView)
win.show()
sys.exit(app.exec_())
