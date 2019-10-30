import sys
import PyQt5.QtWidgets as qtw
import datavis as dv
import emvis as emv

# Read the input filename from first argument
imgPath = sys.argv[1]
app = qtw.QApplication(sys.argv)
win = qtw.QMainWindow()

# Create the image model and view
data = emv.utils.ImageManager().getData(imgPath)

if len(data.shape) == 2:
	imgModel = dv.models.ImageModel(data=data)
	imgView = dv.views.ImageView(model=imgModel, parent=win,
                                 histogram=True)
elif len(data.shape) == 3:
	imgModel = dv.models.SlicesModel(data=data)
	imgView = dv.views.SlicesView(model=imgModel, parent=win,
                                  histogram=True)
else:
    raise Exception("Unsupported data dimensions.")

win.setCentralWidget(imgView)
win.show()
sys.exit(app.exec_())
