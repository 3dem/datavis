#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import PyQt5.QtWidgets as qtw

from datavis.widgets import PagingInfo, PageBar

app = qtw.QApplication(sys.argv)

pagingInfo = PagingInfo(23514, 1000)

# Test some methods of pagingInfo
assert pagingInfo.numberOfPages == 24, ("Wrong number of pages: %s"
                                        % pagingInfo.numberOfPages)
assert pagingInfo.currentPage == 1, "Current page should be 1 now"
assert not pagingInfo.prevPage(), "Previous should not change page now"
assert pagingInfo.nextPage(), "Should move to next page"
assert pagingInfo.currentPage == 2, "After next page should be 2"

pageBar = PageBar(pagingInfo=pagingInfo)

# Create window with ImageView widget
win = qtw.QMainWindow()
win.setCentralWidget(pageBar)
win.show()
win.setWindowTitle('Testing paging...')

sys.exit(app.exec_())
