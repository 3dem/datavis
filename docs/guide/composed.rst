Composed Views
==============

VolumeModel
-----------
3D array-like data array is represented by the :class:`~datavis.models.VolumeModel` model class.
Data is logically represented through 3 axis: AXIS_X, AXIS_Y, AXIS_Z. If we inspect the data
through one of the axis, then it can be viewed as a SlicesModel. For that, the VolumeModel class
has the convenience method :meth:`~data.models.VolumeModel.getSlicesModel` that returns an
:class:`~datavis.models.SlicesModel` instance for the given axis. Additionally, the data for a
specific slice within an axis can be accessed through methods:
:meth:`~data.models.VolumeModel.getSliceData` and :meth:`~data.models.VolumeModel.getSliceImageModel`.

TODO: Code example.

VolumeView
----------

The :class:`~datavis.views.VolumeView` use a VolumeModel as the underlying data model and
it basically makes a composition of two other views: :class:`~datavis.views.MultiSliceView`
and :class:`~datavis.views.GalleryView`. The first one, allows to move around slices for all
the 3 axis at the same time, while in the GalleryView, it is possible to see all slices
of the selected axis. Then, the user can switch between both views.

The following script shows how to implement a simple volume viewer:

.. literalinclude:: composed_example1.py
    :linenos:

It basically create a new VolumeView from the volume file that is passed as the first
argument. The :class:`~datavis.models.VolumeModel` is created by the function
:meth:`~emvis.ModelsFactory.createVolumeModel` that use internally ``emcore`` to read
the volume data. In line 7, we use by default the SLICES view, but if '--gallery' is
provided as argument, we set the GALLERY view.

If we run the script as in the command below, providing an input volume, and with and
without the '--gallery' option, we should have a window similar to the one below.

.. figure:: /images/volumeview.png
    :align: center


DataView
--------

The :class:`~datavis.views.DataView` class is another composed view. It presents data from
:class:`~datavis.models.TableModel` by composing three other views:

* :class:`~datavis.views.ItemsView` Each row from the table is show at a time. All column values
  shown in this view as rows and it is possible to render one of them.
* :class:`~datavis.views.ColumnsView` Many rows are shown in a given page. It is possible
  to select which columns are visible and which ones will be renderer (if possible).
* :class:`~datavis.views.GalleryView` One of the renderable columns is used to show
  rows as an image gallery. Many column values can be displayed as labels under each
  image.

Configuration settings for each of these views can be passed to
:meth:`DataView.__init__ <datavis.views.DataView.__init__>` in the keyword arguments.