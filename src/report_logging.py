from pathlib import Path

import logging
from typing import Iterable

LOGGER = logging.getLogger('main_logger')
MESSAGE_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_TIME_FORMAT = "%I:%M:%S %p"


def __get_default_console_handler() -> logging.StreamHandler:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = __get_default_formatter()
    console_handler.setFormatter(formatter)
    return console_handler


def __get_default_formatter() -> logging.Formatter:
    formatter = logging.Formatter(fmt=MESSAGE_FORMAT, datefmt=DATE_TIME_FORMAT)
    return formatter


def init_logger():
    LOGGER.setLevel(logging.INFO)
    console_handler = __get_default_console_handler()
    LOGGER.addHandler(console_handler)

init_logger()


class ReportsStatistics(object):

    def __init__(self, reports_paths: Iterable[Path]):
        number_of_reports = len(list(reports_paths))
        self.__number_of_reports = number_of_reports
        self.__number_of_fails = 0
        self.__number_of_successes = number_of_reports

    @property
    def number_of_reports(self):
        return self.__number_of_reports

    @property
    def number_of_fails(self):
        return self.__number_of_fails

    @property
    def number_of_successes(self):
        self.__number_of_successes = self.__number_of_reports - self.__number_of_fails
        return self.__number_of_successes

    def inc_counter_of_fails(self):
        self.__number_of_fails += 1


class ReportEventMessageBuilder(object):

    def __init__(self, report_name: str, report_index: int,
                 report_statistics: ReportsStatistics):
        self.__header = "Report %s" % report_name
        self.__counter = "(%d/%d)" % (report_index, report_statistics.number_of_reports)

    def create_message(self, core_text: str):
        return "%s %s %s" % (self.__header, core_text, self.__counter)
