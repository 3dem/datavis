
import unittest
import numpy as np

import datavis as dv


class TestTableModels(dv.tests.TestBase):
    __title = "SimpleModel example"

    class SimpleTableModelImpl(dv.models.SimpleTableModel):
        """ Implementation of SimpleTableModel """
        def __init__(self):
            ColInfo = dv.models.ColumnInfo
            TYPE_INT = dv.models.TYPE_INT
            TYPE_STR = dv.models.TYPE_STRING
            TYPE_FLOAT = dv.models.TYPE_FLOAT
            dv.models.SimpleTableModel.__init__(self,
                                                [ColInfo('col1',
                                                         dataType=TYPE_STR),
                                                 ColInfo('col2',
                                                         dataType=TYPE_INT),
                                                 ColInfo('col3',
                                                         dataType=TYPE_FLOAT)])



    def getDataPaths(self):
        return []

    def test_ColumnInfo(self):
        ColInfo = dv.models.ColumnInfo
        colInfo = ColInfo('column1', dv.models.TYPE_INT)
        self.assertEqual(colInfo.getName(), 'column1',
                         'Column name should be column1')
        self.assertEqual(colInfo.getType(), dv.models.TYPE_INT,
                         'Column type shloud be TYPE_INT(%d)'
                         % dv.models.TYPE_INT)

        print('test_ColumnInfo: OK')

    def test_ColumnConfig(self):
        ColConfig = dv.models.ColumnConfig
        VISIBLE = dv.models.VISIBLE
        VISIBLE_RO = dv.models.VISIBLE_RO
        RENDERABLE = dv.models.RENDERABLE
        RENDERABLE_RO = dv.models.RENDERABLE_RO
        EDITABLE = dv.models.EDITABLE
        EDITABLE_RO = dv.models.EDITABLE_RO

        prop = {
            VISIBLE: True,
            VISIBLE_RO: False,
            RENDERABLE: False,
            RENDERABLE_RO: True,
            EDITABLE: True,
            EDITABLE_RO: True,
            'label': 'column1',
            dv.models.DESCRIPTION: 'Description of column1'
        }

        c = ColConfig('Column1', dv.models.TYPE_INT, **prop)

        self.assertTrue(c[VISIBLE], 'The VISIBLE property should be True')
        self.assertFalse(c[VISIBLE_RO],
                         'The VISIBLE_RO property should be False')
        self.assertFalse(c[RENDERABLE],
                         'The RENDERABLE property should be False')
        self.assertTrue(c[RENDERABLE_RO],
                        'The RENDERABLE_RO property should be True')
        self.assertTrue(c[EDITABLE], 'The EDITABLE property should be True')
        self.assertTrue(c[EDITABLE_RO],
                        'The EDITABLE_RO property should be True')
        c[VISIBLE] = False
        self.assertFalse(c[VISIBLE], 'The VISIBLE property should be False')
        c[VISIBLE_RO] = True
        self.assertTrue(c[VISIBLE_RO], 'The VISIBLE_RO property should be True')
        c[RENDERABLE] = True
        self.assertTrue(c[RENDERABLE], 'The RENDERABLE property should be True')
        c[RENDERABLE_RO] = False
        self.assertFalse(c[RENDERABLE_RO],
                         'The RENDERABLE_RO property should be False')
        c[EDITABLE] = False
        self.assertFalse(c[EDITABLE], 'The EDITABLE property should be False')
        c[EDITABLE_RO] = False
        self.assertFalse(c[EDITABLE_RO],
                         'The EDITABLE_RO property should be False')
        self.assertEqual(c.getLabel(), 'column1',
                         'The label value should be column1')
        self.assertEqual(c.getDescription(), 'Description of column1',
                         'The description should be Description of column1')

        print('test_ColumnConfig: OK')

    def test_SimpleTableModel(self):
        ColInfo = dv.models.ColumnInfo
        TYPE_INT = dv.models.TYPE_INT
        TYPE_STR = dv.models.TYPE_STRING
        TYPE_FLOAT = dv.models.TYPE_FLOAT
        model = dv.models.SimpleTableModel([ColInfo('col1', dataType=TYPE_STR),
                                            ColInfo('col2', dataType=TYPE_INT),
                                            ColInfo('col3',
                                                    dataType=TYPE_FLOAT)])

        self.assertEqual(model.getColumnsCount(), 3,
                         'The columns count should be 3')

        for i, c in enumerate(model.iterColumns()):
            self.assertEqual(c.getName(), 'col%d' % (i+1),
                             'The column name should be col%d' % (i+1))

        model.addRow(['elem(0,0)', 1, 1.0])
        self.assertEqual(model.getValue(0, 0), 'elem(0,0)',
                         'Should be elem(0,0)')
        self.assertEqual(model.getValue(0, 1), 1, 'Should be 1')
        self.assertEqual(model.getValue(0, 2), 1.0, 'Should be 1.0')

        model.addRow(['elem(1,0)', 2, 2.0])
        self.assertEqual(model.getValue(1, 0), 'elem(1,0)',
                         'Should be elem(1,0)')
        self.assertEqual(model.getValue(1, 1), 2, 'Should be 2')
        self.assertEqual(model.getValue(1, 2), 2.0, 'Should be 2.0')

        model.addRow(['elem(2,0)', 3, 3.0])
        self.assertEqual(model.getValue(2, 0), 'elem(2,0)',
                         'Should be elem(2,0)')
        self.assertEqual(model.getValue(2, 1), 3, 'Should be 3')
        self.assertEqual(model.getValue(2, 2), 3.0, 'Should be 3.0')

        model.addRow(['elem(3,0)', 4, 4.0])
        self.assertEqual(model.getValue(3, 0), 'elem(3,0)',
                         'Should be elem(3,0)')
        self.assertEqual(model.getValue(3, 1), 4, 'Should be 4')
        self.assertEqual(model.getValue(3, 2), 4.0, 'Should be 4.0')

        self.assertEqual(model.getRowsCount(), 4, 'Should be 4')

        print('test_SimpleTableModel: OK')

    def test_SlicesTableModel(self):
        s = 5, 1, 1  # 5 slices of dim=(1,1)
        data = np.arange(5)
        data = data.reshape(s)

        sm = dv.models.SlicesModel(data)
        st = dv.models.SlicesTableModel(sm, 'Data')

        for i in range(s[0]):
            self.assertEqual(st.getData(i, 0)[0][0], i,
                             'Data value should be %d' % i)

        print('test_SlicesTableModel: OK')


if __name__ == '__main__':
    unittest.main()
