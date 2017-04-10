from unittest import TestCase

from src.util.strings import ReportString
from src.util import collections


class TestReportString(TestCase):

    def setUp(self):
        self.__str = "Blood Pressure"
        self.__report_str = ReportString(self.__str)

    def testAsString(self):
        expected = self.__str
        actual = str(self.__report_str)
        self.assertEqual(expected, actual)

    def testMatches(self):
        pattern = "B[a-z]+ P[a-z]+"
        self.__report_str.matches(pattern)

    def testAsValue(self):
        value_str = "120 mm"
        actual = ReportString(value_str).as_value()
        expected = 120., "mm"
        self.assertTrue(collections.are_equal(expected, actual))

    def testAsEntry(self):
        entry_str = "key:value"
        actual = ReportString(entry_str).as_entry()
        expected = "key", "value"
        self.assertTrue(collections.are_equal(expected, actual))

    def testStartsWith(self):
        self.assertTrue(self.__report_str.starts_with("Blood"))

    def testCaseInsensitiveStartWith(self):
        case_insensitive_str = self.__report_str.case_insensitive()
        self.assertTrue(case_insensitive_str.starts_with("blood"))

    def testCutHeader(self):
        report_str = self.__report_str
        start = "Blood"
        actual = report_str
        if report_str.starts_with(start):
            actual = report_str.cut_header(len(start))
        expected = "Pressure"
        self.assertEqual(expected, actual)
