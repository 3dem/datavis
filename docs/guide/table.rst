Table Model and related Views
=============================


TableModel
----------

Another central piece of the ``datavis`` and ``emvis`` libraries is the manipulation and visualization
of different kinds of tabular data. This type of information is often used with in many scientific domains
and specifically to CryoEM data processing.

:class:`~datavis.models.TableModel` is the base class that defines the basic methods
required to operate with such tabular data. In that way, this class is a bridge
between the GUI components and different data sources that contains one or many
tables (e.g databases, xml files, csv files, etc).

A TableModel instance provides access to a given data source. The
:meth:`~datavis.models.TableModel.getTableNames` returns the names of the available
tables in that data source. Usually, the TableModel have one table loaded, which
name can be obtained with the :meth:`~datavis.models.TableModel.getTableName`. When
the :meth:`~datavis.models.TableModel.loadTable` is invoked with a table name as
input, it will be loaded and it will become the current active table.

For a given table, the TableModel model allows to iterate over its columns and
rows (:meth:`~datavis.models.TableModel.iterColumns` method ). Table columns'
information is represented by the :class:`~datavis.models.ColumnInfo`
class, that stores basic properties such as column name and type. It is also possible
to access a given cell value at the position (row, col) by using
:meth:`~datavis.models.TableModel.getValue`. If there is associated binary data
(e.g an image) for a given cell, it should be retrieved from the model via the
:meth:`~datavis.models.TableModel.getData` method.


ColumnConfig and TableConfig
----------------------------
The information that is provided by a TableModel can be displayed in different ways.
It can be selected which columns are shown or not, in which order or which data cells
are rendered by default. All this visualization configuration is specified by using
the :class:`~datavis.models.ColumnConfig` and :class:`~datavis.models.TableConfig` classes.

:class:`~datavis.models.ColumnConfig` inherits from ColumnInfo and add more properties
related to the display. For example, it contains a label, that can be different from column
name, and will be used for the text shown with the column. All the options can be passed
as keyword arguments to :meth:`ColumnConfig.__init__ <datavis.models.ColumnConfig.__init__>`.

Then, the :class:`~datavis.models.TableConfig` is used to group several ColumnConfig
related to an underlying TableModel. In that way, the same model can be used in
different contexts and its information visualized in different ways. In the next
sections examples will be provided about how to use these two classes with each
specific view.

ItemsView
---------
This view will show one item at a time. Each item showed corresponds to one
row from the :class:`~datavis.models.TableModel`. All values from that row
are displayed in a single table. When creating a new instance with
:meth:`ItemsView.__init__ <datavis.views.ItemsView>`, the *displayConfig*
parameter allows to pass a :class:`~datavis.models.TableConfig` to specify
which columns will be shown from each row and which one will be rendered
(only one column can be rendered for this view now).

TODO: Code example

.. image:: https://raw.githubusercontent.com/wiki/3dem/datavis/images/itemsview.png?token=ACAM6WD5QAJIDTOPHD3BNHS5YF3K4
    :width: 600px
    :align: center

ColumnsView
-----------
If we want to shows many data rows per page at the same time, then the
:class:`~datavis.views.ColumnsView` is the right choice. It also uses
a TableModel to display rows and columns cell data. An input
:class:`~datavis.models.TableConfig` can be used to specify which columns
will be visible and which ones will be rendered.

TODO: Code example

.. figure:: https://raw.githubusercontent.com/wiki/3dem/datavis/images/columnsview1.png?token=ACAM6WDYBP2F2LNHRRDQ6YK5YF4ME
    :width: 600px
    :align: center

    Example of ColumnsView, all columns are visible and no one is rendered.

.. figure:: https://raw.githubusercontent.com/wiki/3dem/datavis/images/columnsview2.png?token=ACAM6WFUWSPZUKBC7GEUZG25YF44Q
    :width: 600px
    :align: center

    Another example of ColumnsView, image column is rendered and some has been hidden.

GalleryView
-----------
The :class:`~datavis.views.GalleryView` view is useful for rendering of of the renderable
column values for many items in a given page. It allows users to take a looks at a glance
to many images. Additionally, using the :class:`~datavis.models.TableConfig` it is possible
to also display some labels together with the image shown. This is also useful to inspect
measurements or labels associated to the image.

TODO: Code example

.. figure:: https://raw.githubusercontent.com/wiki/3dem/datavis/images/galleryview1.png?token=ACAM6WAOHWKYMLWRODH3XD25YF5DG
    :width: 600px
    :align: center

    Example of GalleryView, image column rendered, no labels

.. figure:: https://raw.githubusercontent.com/wiki/3dem/datavis/images/galleryview2.png?token=ACAM6WEZV54AXWHGRD54S6S5YF5FU
    :width: 600px
    :align: center

    Another example of GalleryView, image column is also rendered, but some columns are used as labels.


