import sys
import datavis as dv
import emvis as emv

# Read the input filename from first argument
volPath = sys.argv[1]
view = dv.views.GALLERY if '--gallery' in sys.argv else dv.views.SLICES

def createView():
    return dv.views.VolumeView(
        parent=None,
        model=emv.models.ModelsFactory.createVolumeModel(volPath),
        toolBar=True,
        view=view,
        slicesMode=dv.models.AXIS_XYZ)

dv.views.showView(createView)
