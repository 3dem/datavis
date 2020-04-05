#!/usr/bin/python
# -*- coding: utf-8 -*-

import datavis as dv


class TestPagingView(dv.tests.TestView):
    __title = "PagingView example"

    def __init__(self, methodName='runTest'):
        self.pagingInfo = dv.widgets.PagingInfo(23514, 1000)
        dv.tests.TestView.__init__(self, methodName=methodName)

    def createView(self):
        return dv.widgets.PageBar(pagingInfo=self.pagingInfo)

    def test_Paging(self):
        print('test_Paging')
        # Test some methods of pagingInfo
        self.assertTrue(self.pagingInfo.numberOfPages == 24,
                        ("Wrong number of pages: %s"
                         % self.pagingInfo.numberOfPages))
        self.assertTrue(self.pagingInfo.currentPage == 1,
                        "Current page should be 1 now")
        self.assertTrue(not self.pagingInfo.prevPage(),
                        "Previous should not change page now")
        self.assertTrue(self.pagingInfo.nextPage(),
                        "Should move to next page")
        self.assertTrue(self.pagingInfo.currentPage == 2,
                        "After next page should be 2")

    def test_PageBar(self):
        print('test_PageBar')


if __name__ == '__main__':
    TestPagingView().runApp()

