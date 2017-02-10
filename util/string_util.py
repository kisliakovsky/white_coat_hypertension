import re


class StringJoiner(object):
    def __init__(self, separator=''):
        self.__separator = separator

    def make(self, x):
        return self.__separator.join(x)


_ENTRY_DELIMITER = ':'


def is_entry(s):
    return _ENTRY_DELIMITER in s


def is_empty_entry(s):
    if is_entry(s):
        return len(s.split(_ENTRY_DELIMITER)[1]) == 0
    else:
        return False


def get_value_of_entry(s):
    if is_entry(s):
        return s.split(_ENTRY_DELIMITER)[1].lstrip().rstrip()


def search_in_str(pattern, string):
    match = re.search(pattern, string)
    if match:
        return match.group()


def cut_if_start_with(substring, s, case_sense=True, trim=False):
    def _cut_if_true(predicate):
        if predicate:
            res = s[len(substring):]
            if trim:
                res = res.lstrip()
            return res
        else:
            return s
    if case_sense:
        return _cut_if_true(s.startswith(substring))
    else:
        return _cut_if_true(s.lower().startswith(substring.lower()))






