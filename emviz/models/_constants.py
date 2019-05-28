
AXIS_X = 0
AXIS_Y = 1
AXIS_Z = 2

DIM_N = -1

# Basic datatype that will be used for visualization
TYPE_BOOL = 0
TYPE_INT = 1
TYPE_FLOAT = 2
TYPE_STRING = 3
# TODO: other possibilities for the future:
# TYPE_URL, TYPE_IMAGE, etc

# ColumnConfig properties constants
VISIBLE = 'visible'
VISIBLE_RO = 'visibleReadOnly'
RENDERABLE = 'renderable'
RENDERABLE_RO = 'renderableReadOnly'
EDITABLE = 'editable'
EDITABLE_RO = 'editableReadOnly'

# FIXME: This should be moved to emviz/core
""" Basic type map between em.Type and current types. """
TYPE_MAP = {
    em.typeBool: TYPE_BOOL,
    em.typeInt8: TYPE_INT,
    em.typeInt16: TYPE_INT,
    em.typeInt32: TYPE_INT,
    em.typeInt64: TYPE_INT,
    em.typeFloat: TYPE_FLOAT,
    em.typeDouble: TYPE_FLOAT,
    em.typeString: TYPE_STRING
}