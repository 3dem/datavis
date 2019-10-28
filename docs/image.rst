Basic Image Models and Views
============================


ImageModel
----------

The :class:`~datavis.models.ImageModel` class is the most basic model, that is essentially a
container of 2D array-like data. It can be initialized completely empty, or some 2D data can be passed.
Following code example is take from a test case::

        import datavis as dv

        # ...
        imgModel = dv.models.ImageModel()  # Empty ImageModel

        # Data and dimensions should be None
        self.assertIsNone(imgModel.getData())
        self.assertIsNone(imgModel.getDim())

We could also initializate the model with some data or use the
:meth:`~datavis.models.ImageModel.setData` after creation. ::

        import numpy as np

        # ...
        data = np.ones((100, 200))
        imgModel.setData(data)

        # Data should not be None, neither dimensions
        self.assertIsNotNone(imgModel.getData())
        self.assertEqual(imgModel.getDim(), (200, 100))
        self.assertEqual(imgModel.getMinMax(), (1, 1))

The ``emcore`` library provides the Image and ImageFile classes to read CryoEM images
from different formats as binary data. In ``emvis``, there are utility classes and function
that use ``emcore`` under-the-hood to read the data. For example, one can easily create
an :class:`ImageModel <datavis.models.ImageModel>` for an image on disk::

    import emvis as emv

    # ...
    im = emv.ImageManager()
    imgModel = dv.models.ImageModel(data=im.getData(imagePath))


ImageView
---------
The :class:`~datavis.views.ImageView` widget use the :class:`~datavis.models.ImageModel` class to retrieve
the data that will be displayed. The current implementation of the ImageView class is based on the
`pyqtgraph.ImageView <http://www.pyqtgraph.org/documentation/widgets/imageview.html?highlight=imageview>`_
class. Throw this widget, our ImageView class supports many display functions such as: zooming, dragging,
axis display and histogram visualization, among others. Many of these options can be set through the
keywords parameters of the :meth:`ImageView.__init__ <datavis.views.ImageView.__init__>` method.

A simple example (image_example.py) that displays a CryoEM image using ImageView is shown below:

.. literalinclude:: image_example.py

Then, we can execute the script passing an input image:

.. code-block:: bash

    python image_example.py relion_tutorial/micrographs/006.mrc

The following image should be shown:

.. image:: https://raw.githubusercontent.com/wiki/3dem/datavis/images/image_view.png?token=ACAM6WB3OLZKRY7B4GYM3VC5YBFC4


SlicesModel and SlicesView
--------------------------


MultiSliceView
--------------

