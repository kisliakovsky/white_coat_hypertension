from typing import Tuple, List, Iterable

import util.string_util as su


def map_with_ops(ops, a_list):
    for op in ops:
        a_list = list(map(op, a_list))
    return a_list


def filter_with_ops(ops, a_list):
    for op in ops:
        a_list = list(filter(op, a_list))
    return a_list


def search_first_in_list(a_list, pattern, remove_after=False, replace_after=None):
    for i, string in enumerate(a_list):
        match = su.search_in_str(pattern, string)
        if match:
            if replace_after:
                a_list[i] = replace_after
                return string
            if remove_after:
                del a_list[i]
                return string
            else:
                return i, string
    if remove_after or replace_after:
        return None
    else:
        return -1, None


def search_sequence_in_list(a_list, header_pattern, num, remove_after=False):
    for i, s in enumerate(a_list):
        header = su.search_in_str(header_pattern, s)
        if header:
            after_seq_index = i + num + 1
            res = a_list[i + 1:after_seq_index]
            if remove_after:
                del a_list[i:after_seq_index]
            return header, res


def search_among_neighbors(a_list, i, neighbor_pattern, remove_after=False):
    prev_index = i - 1
    next_index = i + 1
    if i > 0:
        match = su.search_in_str(neighbor_pattern, a_list[prev_index])
        if match:
            res = a_list[prev_index]
            if remove_after:
                del a_list[prev_index:next_index]
            return prev_index, res
    if next_index < len(a_list):
        match = su.search_in_str(neighbor_pattern, a_list[next_index])
        if match:
            res = a_list[next_index]
            if remove_after:
                del a_list[i:next_index + 1]
            return next_index, res


def split_list(lst: List, lengths: Iterable[int]) -> List:
    res = []
    for length in lengths:
        res.append(lst[0: length])
        lst = lst[length:]
    return res


def compare_lists(a: List, b: List) -> bool:
    """
    compare lists
    :param a: the first list
    :param b: the second list
    :return: True if lists are equal, otherwise False
    """
    return len(a) == len([i for i, j in zip(a, b) if i == j])


def filter_list_by_value(lst: List, val) -> List:
    return [x for x in lst if x != val]
