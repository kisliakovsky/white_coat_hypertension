from unittest import TestCase

from src.util import list_util as lutil


class TestListUtil(TestCase):

    def testSplitList(self):
        lst = list(range(1, 10 + 1))
        res = lutil.split_list(lst, (1, 2, 3, 4))
        expected = [7, 8, 9, 10]
        self.assertTrue(lutil.compare_lists(expected, res[3]))

    def testCompareLists(self):
        a = [1, 2, 3]
        b = [1, 2, 3]
        self.assertTrue(lutil.compare_lists(a, b))
