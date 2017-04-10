from unittest import TestCase

from src.util import collections
from src.util.collections import ReportBlock, Block


class TestBlocks(TestCase):

    _TWO_THREE_DIGITS_NUM_PATTERN = r"^\d{2,3}$"

    def testAreEqual(self):
        a = [1, 2, 3]
        b = [1, 2, 3]
        self.assertTrue(collections.are_equal(a, b))

    def testSplitList(self):
        some_range = list(range(1, 10 + 1))
        parts_length = tuple(range(1, 4 + 1))
        range_block = Block(some_range)
        parts = range_block.divide_into_parts(parts_length)
        actual = parts[3]
        expected = [7, 8, 9, 10]
        self.assertTrue(collections.are_equal(expected, actual))

    def testFilterByItems(self):
        some_range = [1, 2, 3, 4]
        start_index = 1
        finish_index = 3
        range_region = some_range[start_index:finish_index]
        range_block = Block(some_range)
        item_generator = range_block.filter_excluding_items(range_region)
        expected = [some_range[start_index - 1]] + some_range[finish_index:]
        actual = list(item_generator)
        self.assertTrue(collections.are_equal(expected, actual))

    def testSearchFirstOccurrenceByPattern(self):
        strings = ["john", "doe", "56", "alex"]
        block = ReportBlock(strings)
        actual = block.search_first_occurrence_by_pattern(TestBlocks._TWO_THREE_DIGITS_NUM_PATTERN)
        expected = 2, "56"
        self.assertTrue(collections.are_equal(expected, actual))

    def testReplaceByIndex(self):
        strings = ["john", "doe", "56", "alex"]
        index = 2
        replacement = "100"
        block = Block(strings)
        block.replace_by_index(index, replacement)
        expected = replacement
        actual = block.inner_list[index]
        self.assertEqual(expected, actual)

    def testRemoveByIndex(self):
        strings = ["john", "doe", "56", "alex"]
        index = 2
        block = Block(strings)
        block.remove_by_index(index)
        expected = ["john", "doe", "alex"]
        actual = block.inner_list
        self.assertTrue(collections.are_equal(expected, actual))

    def testRemoveByIndices(self):
        strings = ["john", "doe", "56", "alex"]
        start_index = 1
        finish_index = 3
        block = Block(strings)
        block.remove_by_indices(start_index, finish_index)
        expected = [strings[start_index - 1]] + strings[finish_index:]
        actual = block.inner_list
        self.assertTrue(collections.are_equal(expected, actual))

    def testSearchSequenceByHeaderPattern(self):
        strings = ["john", "cindy", "alex", "56"]
        header = "names"
        header_pattern = "^%s$" % header
        strings = [header] + strings
        block = ReportBlock(strings)
        sequence_start_index = 1
        sequence_length = 3
        header, names = block.search_sequence_by_header_pattern(header_pattern, sequence_length)
        expected = strings[sequence_start_index:sequence_start_index + sequence_length]
        self.assertTrue(collections.are_equal(expected, names))

    def testSearchAmongNeighbors(self):
        strings = ["names", "john", "cindy", "alex", "56"]
        block = ReportBlock(strings)
        actual = block.search_among_neighbors(3, TestBlocks._TWO_THREE_DIGITS_NUM_PATTERN)
        expected = (4, strings[4])
        self.assertTrue(collections.are_equal(expected, actual))
