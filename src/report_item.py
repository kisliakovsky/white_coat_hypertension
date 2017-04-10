import re
from enum import Enum
from typing import Tuple, Union, List

from src.util import math_util as mutil
from src.util.collections import Block
from src.util.strings import ENTRY_DELIMITER, VALUE_DELIMITER

_PATIENT_ID_LEN_BOUND = (3, 10)


class ReportItemPattern(Enum):
    TITLE = r"[Rr]eport"
    PHYSICIAN_ENTRY = r"[Pp]hysician"
    DATE = r"\d+.\d+.\d{4}"
    TIME = r"\d+:\d{2}$"
    WHITESPACE = r"^\s*$"
    PERIOD = r"[Pp]eriod"
    STUDY_DATE = r"[Ss]tudy [Dd]ate"
    AWAKE_ASLEEP = r"wake.*sleep"
    BLOOD_PRESSURE_THRESHOLD = r"[Bb][Pp] [Tt]hreshold"
    BLOOD_PRESSURE_LOAD = r"[Bb][Pp] [Ll]oad"
    PAGINATOR = r"[Pp]age.*of.*"
    READINGS = r"^[Rr]eadings$"
    TOTAL_READINGS = r"[Tt]otal [Rr]eadings"
    SUCCESSFUL_READINGS = r"\d+\s*\(\d+.*%\)"
    PATIENT_ID = r"^\d{%d,%d}$" % _PATIENT_ID_LEN_BOUND
    PATIENT_NAME = r"[\w\.]+ \w+"
    PATIENT_SEX = r"^([Ff]em|[Mm])ale$"
    DATE_TIME_SYS = r"[Dd]ate.*/.*[Tt]ime.*[Ss]ys"
    HEART_RATE = r"^HR$"
    SYSTOLIC = r"^Sys$"
    DIASTOLIC = r"^Dia$"
    AVG_BLOOD_PRESSURE = r"[Aa]verage [Bb]lood [Pp]ressure"
    TWENTY_FOUR_HOURS = r"24-h.*"
    AWAKE = r"^Awake$"
    ASLEEP = r"^Asleep$"
    MAP_PP = r"[Mm][Aa][Pp] [Pp][Pp]"
    TWO_THREE_DIGITS_NUM = r"^\d{2,3}$"
    START_NUM = r"^\d"
    PARENTHESES_NUM = r"^\(\d+\)$"
    COMMA_NUM = r"^\d+,\d+$"
    WHITE_COAT_WINDOW = r"[Ww]hite [Cc]oat [Ww]indow"
    FIRST_HOUR = r"1st.*h.*[Mm]ax"
    NIGHT_TIME_DIP = r"[Nn]ight.*[Dd]ip.*%"
    DIP = r"^[Dd]ip%$"
    PERIOD_TIME = r"^[Tt]ime$"
    PERIOD_INTERVAL = r"^[Ii]nterval$"
    BREAK = r"^break$"

    def as_string(self):
        return self.value


class ReportItemKey(Enum):
    TIME = "time"
    INTERVAL = "interval"
    DAY = "day"
    NIGHT = "night"
    TOTAL_READINGS = "total"
    SUCCESSFUL_READINGS = "success"
    WHITE_COAT_WINDOW = "wcw"
    DATETIME = "dt"
    SYSTOLIC = "sys"
    DIASTOLIC = "dia"
    HEART_RATE = "hr"
    MEAN_ARTERIAL_PRESSURE = "map"
    PULSE_PRESSURE = "pp"
    TWENTY_FOUR_HOURS = "24h"
    AWAKE = "awake"
    ASLEEP = "asleep"
    READINGS = "readings"
    FIRST_HOUR = "first_hour"
    DIP = "dip"
    NIGHT_TIME_DIP = "ntd"
    BREAK = "break"

    def as_string(self):
        return self.value


class ReportItem(Enum):

    PERIOD_TIME = ReportItemKey.TIME, ReportItemPattern.PERIOD_TIME
    PERIOD_INTERVAL = ReportItemKey.INTERVAL, ReportItemPattern.PERIOD_INTERVAL
    TOTAL_READINGS = ReportItemKey.TOTAL_READINGS, ReportItemPattern.TOTAL_READINGS
    SUCCESSFUL_READINGS = ReportItemKey.SUCCESSFUL_READINGS, ReportItemPattern.SUCCESSFUL_READINGS
    SYSTOLIC = ReportItemKey.SYSTOLIC, ReportItemPattern.SYSTOLIC
    DIASTOLIC = ReportItemKey.DIASTOLIC, ReportItemPattern.DIASTOLIC
    HEART_RATE = ReportItemKey.HEART_RATE, ReportItemPattern.HEART_RATE
    WHITE_COAT_WINDOW = ReportItemKey.WHITE_COAT_WINDOW, ReportItemPattern.WHITE_COAT_WINDOW
    NIGHT_TIME_DIP = ReportItemKey.NIGHT_TIME_DIP, ReportItemPattern.NIGHT_TIME_DIP

    def __new__(cls, key: ReportItemKey, pattern: ReportItemPattern):
        obj = object.__new__(cls)
        obj._value_ = key, pattern
        return obj

    def __init__(self, key: ReportItemKey, pattern: ReportItemPattern):
        self.__key = key
        self.__pattern = pattern

    @property
    def key(self) -> ReportItemKey:
        return self.__key

    @property
    def pattern(self) -> ReportItemPattern:
        return self.__pattern


class _SensitiveCaseReportString(object):

    def __init__(self, string: str):
        self.__string = string

    def __str__(self):
        return self.__string

    def starts_with(self, substring: str) -> bool:
        return str(self).startswith(substring)


class _InsensitiveCaseReportString(_SensitiveCaseReportString):

    def __init__(self, string: str):
        super().__init__(string.lower())

    def starts_with(self, substring: str) -> bool:
        return str(self).startswith(substring.lower())


class ReportString(object):

    def __init__(self, string: str):
        self.__string = string
        self.__sensitive_case_string = _SensitiveCaseReportString(string)

    def __str__(self):
        return self.__string

    def __bool__(self):
        return bool(self.__string)

    def matches(self, pattern: ReportItemPattern) -> str:
        pattern_str = pattern.as_string()
        match = re.search(pattern_str, self.__string)
        if match:
            return match.group()

    def __has_entry_delimiter(self) -> bool:
        return ENTRY_DELIMITER in self.__string

    def __has_value_delimiter(self) -> bool:
        return VALUE_DELIMITER in self.__string

    def as_value(self) -> Tuple[Union[float, str], str]:
        if self.__has_value_delimiter():
            value = self.__string.split(VALUE_DELIMITER)
            quantity = mutil.try_float_cast(value[0])
            unit = value[1]
            return quantity, unit

    def as_entry(self) -> Tuple[str, str]:
        if self.__has_entry_delimiter():
            entry = self.__string.split(ENTRY_DELIMITER)
            key = entry[0].lstrip().rstrip()
            value = entry[1].lstrip().rstrip()
            return key, value

    def starts_with(self, substring: str) -> bool:
        return self.__sensitive_case_string.starts_with(substring)

    def cut_header(self, number_of_cut_symbols: int) -> str:
        return self.__string[number_of_cut_symbols:].lstrip()

    def case_insensitive(self) -> _InsensitiveCaseReportString:
        return _InsensitiveCaseReportString(self.__string)


class ReportBlock(Block[str]):

    def search_first_occurrence_by_pattern(
            self, pattern: ReportItemPattern) -> Tuple[Union[int, None], ReportString]:
        for i, string in enumerate(self.inner_list):
            report_string = ReportString(string)
            if report_string.matches(pattern):
                return i, report_string
        return None, ReportString("")

    def remove_item(self, pattern: ReportItemPattern) -> ReportString:
        return self.search_first_occurrence_by_pattern_and_remove(pattern)

    def search_first_occurrence_by_pattern_and_remove(self,
                                                      pattern: ReportItemPattern) -> ReportString:
        i, report_string = self.search_first_occurrence_by_pattern(pattern)
        self.remove_by_index(i)
        return report_string

    def replace_item(self, pattern: ReportItemPattern, replacement: str) -> ReportString:
        return self.search_first_occurrence_by_pattern_and_replace(pattern, replacement)

    def search_first_occurrence_by_pattern_and_replace(self, pattern: ReportItemPattern,
                                                       replacement: str) -> ReportString:
        i, report_string = self.search_first_occurrence_by_pattern(pattern)
        self.replace_by_index(i, replacement)
        return report_string

    def _search_neighbor(self, neighbor_index: int,
                         neighbor_pattern: ReportItemPattern) -> ReportString:
        neighbor_str = self.inner_list[neighbor_index]
        neighbor_report_str = ReportString(neighbor_str)
        if neighbor_report_str.matches(neighbor_pattern):
            return neighbor_report_str

    def search_among_neighbors(self, item_index: int,
                               neighbor_pattern: ReportItemPattern) -> Tuple[int, ReportString]:
        left_neighbor_index = item_index - 1
        right_neighbor_index = item_index + 1
        neighbor_index = None
        neighbor_report_string = ReportString("")
        if item_index > 0:
            neighbor_index = left_neighbor_index
            neighbor_report_string = self._search_neighbor(neighbor_index, neighbor_pattern)
            if neighbor_report_string is not None:
                return neighbor_index, neighbor_report_string
        if right_neighbor_index < len(self.inner_list):
            neighbor_index = right_neighbor_index
            neighbor_report_string = self._search_neighbor(neighbor_index, neighbor_pattern)
            if neighbor_report_string is not None:
                return neighbor_index, neighbor_report_string
        return neighbor_index, neighbor_report_string

    def search_among_neighbors_and_remove(self, item_index: int,
                                          neighbor_pattern:
                                          ReportItemPattern) -> ReportString:
        left_neighbor_index = item_index - 1
        right_neighbor_index = item_index + 1
        neighbor_report_string = ReportString("")
        if item_index > 0:
            neighbor_index = left_neighbor_index
            neighbor_report_string = self._search_neighbor(neighbor_index, neighbor_pattern)
            if neighbor_report_string is not None:
                self.remove_by_indices(neighbor_index, neighbor_index + 2)
                return neighbor_report_string
        if right_neighbor_index < len(self.inner_list):
            neighbor_index = right_neighbor_index
            neighbor_report_string = self._search_neighbor(neighbor_index, neighbor_pattern)
            if neighbor_report_string is not None:
                self.remove_by_indices(neighbor_index - 1, neighbor_index + 1)
                return neighbor_report_string
        return neighbor_report_string

    def _search_sequence_indices_by_header_pattern(self, header_pattern: ReportItemPattern,
                                                   sequence_length: int) -> Tuple[int, int, int]:
        header_index, header = self.search_first_occurrence_by_pattern(header_pattern)
        if header_index is not None:
            start_sequence_index = header_index + 1
            finish_sequence_index = header_index + sequence_length + 1
            return header_index, start_sequence_index, finish_sequence_index

    def search_sequence_by_header_pattern(self, header_pattern: ReportItemPattern,
                                          sequence_length: int) -> Tuple[str, List[str]]:
        indices = self._search_sequence_indices_by_header_pattern(header_pattern, sequence_length)
        header_index, start_sequence_index, finish_sequence_index = indices
        header = self.inner_list[header_index]
        sequence = self.inner_list[start_sequence_index:finish_sequence_index]
        return header, sequence

    def search_sequence_by_header_pattern_and_remove(self, header_pattern: ReportItemPattern,
                                                     sequence_length: int) -> List[str]:
        indices = self._search_sequence_indices_by_header_pattern(header_pattern, sequence_length)
        header_index, start_sequence_index, finish_sequence_index = indices
        sequence = self.inner_list[start_sequence_index:finish_sequence_index]
        self.remove_by_indices(header_index, finish_sequence_index)
        return sequence
