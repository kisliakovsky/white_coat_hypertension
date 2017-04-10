from typing import List, TypeVar, Union
import numpy as np


def parse_quantity(s):
    res = s.split(' ')
    if len(res) == 2:
        return {
            "value": res[0],
            "unit": res[1]
        }


def try_float_cast(s: str) -> Union[float, str]:
    try:
        return float(s)
    except ValueError:
        return s


def split_list_by_values(numbers):
    min_list = []
    max_list = []
    min_val = min(numbers)
    max_val = max(numbers)
    for n in numbers:
        delta_min = calc_delta(n, min_val)
        delta_max = calc_delta(n, max_val)
        if delta_min < delta_max:
            min_list.append(n)
        else:
            max_list.append(n)
    return min_list, max_list


def calc_delta(value, const):
    return abs(value - const)


def _calc_msd_term(current_number, next_number):
    return (next_number - current_number) ** 2


def _calc_msd_terms(numbers):
    last_index = len(numbers) - 1
    for i in range(last_index):
        yield _calc_msd_term(numbers[i], numbers[i + 1])


def msd(numbers: List[int]) -> float:
    n = len(numbers)
    if n < 2:
        return 0
    else:
        msd_terms = _calc_msd_terms(numbers)
        msd_terms_sum = sum(msd_terms)
        return np.sqrt(msd_terms_sum / (n - 2))


def mean(numbers):
    return float(sum(numbers)) / max(len(numbers), 1)


class ReportStatistics(object):

    def __init__(self, numbers):
        self.__numbers = numbers

    # TODO: try to replace with numpy mean()
    @staticmethod
    def calc_mean(numbers):
        return float(sum(numbers)) / max(len(numbers), 1)

    @staticmethod
    def _calc_msd_term(current_number, next_number):
        return (next_number - current_number) ** 2

    @staticmethod
    def _calc_msd_terms(numbers):
        last_index = len(numbers) - 1
        for i in range(last_index):
            yield ReportStatistics._calc_msd_term(numbers[i], numbers[i + 1])

    @staticmethod
    def calc_msd(numbers: List[int]) -> float:
        n = len(numbers)
        if n < 2:
            return 0
        else:
            msd_terms = ReportStatistics._calc_msd_terms(numbers)
            msd_terms_sum = sum(msd_terms)
            return np.sqrt(msd_terms_sum / (n - 2))

    @staticmethod
    def _calc_delta(value, const):
        return np.abs(value - const)

    @staticmethod
    def split_numbers_by_values(numbers):
        min_list = []
        max_list = []
        min_val = min(numbers)
        max_val = max(numbers)
        for n in numbers:
            delta_min = calc_delta(n, min_val)
            delta_max = calc_delta(n, max_val)
            if delta_min < delta_max:
                min_list.append(n)
            else:
                max_list.append(n)
        return min_list, max_list

    def mean(self):
        return ReportStatistics.calc_mean(self.__numbers)

    def msd(self):
        return ReportStatistics.calc_mean(self.__numbers)

    def split_by_values(self):
        return ReportStatistics.split_numbers_by_values(self.__numbers)
