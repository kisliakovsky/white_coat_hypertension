from pathlib import Path
from typing import List, Iterable, Tuple, Callable, Any
from datetime import timedelta as TimeDelta
from datetime import datetime

import numpy as np
from matplotlib import pyplot, dates

from src.patient import Patient
from src.report_logging import LOGGER
from src.util import paths
from src.util.paths import Extension

_DATE_FORMAT = "%d.%m.%Y"
_TIME_FORMAT = "%H:%M"
_DATETIME_FORMAT = "%s %s" % (_DATE_FORMAT, _TIME_FORMAT)
_TIME_INTERVAL = TimeDelta(minutes=15)
_START_TIME = datetime.strptime("01.01.1970 8:00", _DATETIME_FORMAT)
_FINISH_TIME = datetime.strptime("02.01.1970 17:00", _DATETIME_FORMAT) + _TIME_INTERVAL
_TIME_PERIOD = _FINISH_TIME - _START_TIME
_TIME_INTERVAL_NUM = int(_TIME_PERIOD / _TIME_INTERVAL)


def get_default_datetimes():
    time_columns = []
    curr_time = _START_TIME
    for i in range(_TIME_INTERVAL_NUM):
        time_columns.append(curr_time)
        curr_time += _TIME_INTERVAL
    return time_columns


DEFAULT_TIMES = get_default_datetimes()

plt = pyplot

_FIGURE_SIZE_KEY = "figure.figsize"
# http://matplotlib.org/users/customizing.html

plt.rcParams[_FIGURE_SIZE_KEY] = 20, 16  # in inches


class IncompleteDataError(Exception):
    pass


class PatientChart(object):

    _saves_counter = 1

    @classmethod
    def inc_counter(cls):
        cls._saves_counter += 1

    _DATE_FORMAT = "%d.%m.%Y"
    _TIME_FORMAT = "%H:%M"
    _DATETIME_FORMAT = "%s %s" % (_DATE_FORMAT, _TIME_FORMAT)

    def __init__(self, patients: List[Patient]):
        groups = PatientChart._group_patients_by_blood_pressure_phenotype(patients)
        self.__groups = groups
        self.__sizes_of_groups = [len(group) for group in groups]

    @property
    def groups(self) -> List[List[Patient]]:
        return self.__groups

    @property
    def sizes_of_groups(self) -> List[int]:
        return self.__sizes_of_groups

    def save_figures(self, basic_output_dir: Path, basic_name: str):
        self.save_common_figure(basic_output_dir, basic_name)
        self.save_avg_figure(basic_output_dir, basic_name)

    def save_common_figure(self, basic_output_dir: Path, basic_name: str):
        self.__save_figure(basic_output_dir, "%s_%s" % (basic_name, "common"),
                           self.__draw_common_plot)

    def save_avg_figure(self, basic_output_dir: Path, basic_name: str):
        self.__save_figure(basic_output_dir, "%s_%s" % (basic_name, "avg"),
                           self.__draw_avg_plot)

    def __save_figure(self, basic_output_dir: Path,
                      basic_name: str, drawer: Callable[['PatientChart', int, Any], None]):
        rows_num = 2
        columns_num = 3
        figure, axes_array = plt.subplots(rows_num, columns_num, sharex=True, sharey=True)
        for i in range(rows_num):
            for j in range(columns_num):
                group_index = j + i * columns_num + 1
                axes = axes_array[i, j]
                drawer(group_index, axes)
                axes.grid()
                x_major_lct = dates.AutoDateLocator(minticks=2, maxticks=10,
                                                    interval_multiples=True)
                x_minor_lct = dates.HourLocator(byhour=range(0, 25, 1))
                x_fmt = dates.AutoDateFormatter(x_major_lct)
                axes.xaxis.set_major_locator(x_major_lct)
                axes.xaxis.set_minor_locator(x_minor_lct)
                axes.xaxis.set_major_formatter(x_fmt)
                for label in axes.get_xmajorticklabels():
                    label.set_rotation(30)
                    label.set_horizontalalignment("right")
        axes_array[0, 0].legend()
        while True:
            new_name = "%s_%d" % (basic_name, self._saves_counter)
            output_path = Path(basic_output_dir, "figures")
            paths.create_dir(output_path)
            output_path = Path(output_path, new_name).with_suffix('.' + Extension.PNG.as_string())
            if output_path.is_file():
                self.inc_counter()
                continue
            else:
                plt.savefig(str(output_path))
                plt.close(figure)
                LOGGER.info("The figure was saved as %s" % output_path.absolute())
                break

    NIGHT_START_TIME = datetime.strptime("01.01.1970 23:00", _DATETIME_FORMAT).time()
    NIGHT_FINISH_TIME = datetime.strptime("02.01.1970 06:00", _DATETIME_FORMAT).time()

    def __draw_common_plot(self, group_index: int, axes):
        group = self.groups[group_index]
        axes.set_title("Phenotype #%d" % group_index)
        axes.set_xlabel("Time")
        axes.set_ylabel("Blood pressure/Heart rate")
        for i, patient in enumerate(group):
            try:
                normalized_values = PatientChart._normalize_values(patient)
            except IncompleteDataError:
                self.__sizes_of_groups[group_index] -= 1
                continue
            datetimes, systolic_bps, diastolic_bps, heart_rates = normalized_values
            if i == 0:
                axes.plot(datetimes, systolic_bps, "r-", label="systolic blood pressure")
                axes.plot(datetimes, diastolic_bps, "b-", label="diastolic blood pressure")
                # axes.plot(datetime, heart_rates, "g-", label="heart rate")
            else:
                axes.plot(datetimes, systolic_bps, "r-")
                axes.plot(datetimes, diastolic_bps, "b-")
                # axes.plot(datetime, heart_rates, "g-")

    def __draw_avg_plot(self, group_index: int, axes):
        group = self.groups[group_index]
        axes.set_title("Phenotype #%d" % group_index)
        axes.set_xlabel("Time")
        axes.set_ylabel("Blood pressure/Heart rate")
        avg_values = self._avg_values(group)
        datetimes, systolic_blood_pressures, diastolic_blood_pressures, heart_rates = avg_values
        axes.plot(datetimes, systolic_blood_pressures, "r-", label="systolic blood pressure")
        axes.plot(datetimes, diastolic_blood_pressures, "b-", label="diastolic blood pressure")
        # axes.plot(datetime, heart_rates, "g-", label="heart rate")

    @staticmethod
    def _normalize_values(patient: Patient) -> Tuple[List[datetime], List[int],
                                                     List[int], List[int]]:
        normalized_datetimes = []
        normalized_systolic_blood_pressures = []
        normalized_diastolic_blood_pressures = []
        normalized_heart_rates = []
        default_datetimes = DEFAULT_TIMES
        index = 0
        measures_datetimes = patient.measures_datetimes
        measures_datetimes_num = len(measures_datetimes)
        for dt in default_datetimes:
            if index < measures_datetimes_num:
                measure_datetime = measures_datetimes[index]
                if measure_datetime.time() == dt.time():
                    systolic_blood_pressure = patient.systolic_blood_pressures[index]
                    diastolic_blood_pressure = patient.diastolic_blood_pressures[index]
                    heart_rate = patient.heart_rates[index]
                    normalized_datetimes.append(dt)
                    normalized_systolic_blood_pressures.append(systolic_blood_pressure)
                    normalized_diastolic_blood_pressures.append(diastolic_blood_pressure)
                    normalized_heart_rates.append(heart_rate)
                    index += 1
                    if (isinstance(systolic_blood_pressure, str)
                        or isinstance(diastolic_blood_pressure, str)
                        or isinstance(heart_rate, str)):
                        raise IncompleteDataError
        return (normalized_datetimes, normalized_systolic_blood_pressures,
                normalized_diastolic_blood_pressures, normalized_heart_rates)

    @staticmethod
    def _avg_values(group: Iterable[Patient]) -> Tuple[List[datetime], List[float],
                                                       List[float], List[float]]:
        datetimes_list = []
        systolic_blood_pressures_list = []
        diastolic_blood_pressures_list = []
        heart_rates_list = []
        for patient in group:
            try:
                normalized_values = PatientChart._normalize_values(patient)
            except IncompleteDataError:
                continue
            datetimes, systolic_bps, diastolic_bps, heart_rates = normalized_values
            datetimes_list.append(datetimes)
            systolic_blood_pressures_list.append(systolic_bps)
            diastolic_blood_pressures_list.append(diastolic_bps)
            heart_rates_list.append(heart_rates)
        default_datetimes = DEFAULT_TIMES
        avg_datetimes = [[] for _ in default_datetimes]
        avg_systolic_blood_pressures = [[] for _ in default_datetimes]
        avg_diastolic_blood_pressures = [[] for _ in default_datetimes]
        avg_heart_rates = [[] for _ in default_datetimes]
        for i, default_datetime in enumerate(default_datetimes):
            for j, datetimes in enumerate(datetimes_list):
                for k, dt in enumerate(datetimes):
                    if dt == default_datetime:
                        avg_datetimes[i].append(dt)
                        systolic_blood_pressures = systolic_blood_pressures_list[j]
                        avg_systolic_blood_pressures[i].append(systolic_blood_pressures[k])
                        diastolic_blood_pressures = diastolic_blood_pressures_list[j]
                        avg_diastolic_blood_pressures[i].append(diastolic_blood_pressures[k])
                        heart_rates = heart_rates_list[j]
                        avg_heart_rates[i].append(heart_rates[k])
        indices = [i for i, avg_datetime in enumerate(avg_datetimes) if avg_datetime]
        filtered_avg_datetimes = []
        filtered_avg_systolic_blood_pressures = []
        filtered_avg_diastolic_blood_pressures = []
        filtered_avg_heart_rates = []
        for index in indices:
            filtered_avg_datetimes.append(avg_datetimes[index][0])
            filtered_avg_systolic_blood_pressures.append(avg_systolic_blood_pressures[index])
            filtered_avg_diastolic_blood_pressures.append(avg_diastolic_blood_pressures[index])
            filtered_avg_heart_rates.append(avg_heart_rates[index])
        avg_datetimes = filtered_avg_datetimes
        avg_systolic_blood_pressures = list(map(np.mean, filtered_avg_systolic_blood_pressures))
        avg_diastolic_blood_pressures = list(map(np.mean, filtered_avg_diastolic_blood_pressures))
        avg_heart_rates = list(map(np.mean, filtered_avg_heart_rates))
        # noinspection PyTypeChecker
        return (avg_datetimes, avg_systolic_blood_pressures,
                avg_diastolic_blood_pressures, avg_heart_rates)

    @staticmethod
    def _group_patients_by_blood_pressure_phenotype(
            patients: Iterable[Patient]) -> List[List[Patient]]:
        number_of_phenotypes = 6
        groups = [[] for _ in range(number_of_phenotypes + 1)]
        for patient in patients:
            group = groups[patient.blood_pressure_phenotype]
            group.append(patient)
        return groups
