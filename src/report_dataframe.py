from datetime import datetime
# noinspection PyPep8Naming
from datetime import timedelta as TimeDelta
from enum import Enum
from pathlib import Path
from typing import Iterable

import numpy as np
from pandas import DataFrame

from src.patient import Patient
from src.report_logging import LOGGER
from src.patient import EMPTY_VALUE_STR
from src.report_item import ReportItemKey
from src.util.collections import Block
from src.util.paths import Extension
from src.util import math_util as mutil, paths


class PatientDataFrameKey(Enum):
    ID = "Id"
    PATIENT_NAME = "Name"
    DATE_OF_BIRTH = "DOB"
    BLOOD_PRESSURE_PHENOTYPE = "BP Phenotype"
    BLOOD_PRESSURE_PROFILE = "BP profile"
    LAST_HOUR_MAX_SYS_BLOOD_PRESSURE_KEY = "Last hour max sBP"
    AVG_DAY_KEY = "Avg BP per day"
    AVG_AWAKE_KEY = "Avg BP while awake"
    AVG_ASLEEP_KEY = "Avg BP while asleep"
    FIRST_HOUR_MAX_KEY = "BP max 1st hour"
    MSD_ALL_SYSTOLIC = "sMSD all"
    MSD_DAY_SYSTOLIC = "sMSD day (07-23)"
    MSD_ALT_DAY_SYSTOLIC = "sMSD day (10-20)"
    MSD_NIGHT_SYSTOLIC = "sMSD night (23-07)"
    MSD_ALT_NIGHT_SYSTOLIC = "sMSD night (00-06)"
    MSD_ALL_DIASTOLIC = "dMSD all"
    MSD_DAY_DIASTOLIC = "dMSD day (07-23)"
    MSD_ALT_DAY_DIASTOLIC = "dMSD day (10-20)"
    MSD_NIGHT_DIASTOLIC = "dMSD night (23-07)"
    MSD_ALT_NIGHT_DIASTOLIC = "dMSD night (00-06)"
    DAY_TIME = "Awake time"
    NIGHT_TIME = "Asleep time"
    EXTRA_TIME = "Extra time"
    SYSTOLIC = "sBP"
    DIASTOLIC = "dBP"
    HEART_RATE = "HR"

    def as_string(self) -> str:
        return self.value


class PatientDataFrame(object):

    _saves_counter = 1

    _SINGLE_KEYS = (PatientDataFrameKey.ID, PatientDataFrameKey.PATIENT_NAME,
                    PatientDataFrameKey.DATE_OF_BIRTH, PatientDataFrameKey.BLOOD_PRESSURE_PHENOTYPE,
                    PatientDataFrameKey.BLOOD_PRESSURE_PROFILE,
                    PatientDataFrameKey.LAST_HOUR_MAX_SYS_BLOOD_PRESSURE_KEY)
    _AVG_KEYS = (PatientDataFrameKey.AVG_DAY_KEY,
                 PatientDataFrameKey.AVG_AWAKE_KEY, PatientDataFrameKey.AVG_ASLEEP_KEY)
    _MSD_KEYS = (PatientDataFrameKey.MSD_ALL_SYSTOLIC,
                 PatientDataFrameKey.MSD_DAY_SYSTOLIC, PatientDataFrameKey.MSD_ALT_DAY_SYSTOLIC,
                 PatientDataFrameKey.MSD_NIGHT_SYSTOLIC, PatientDataFrameKey.MSD_ALT_NIGHT_SYSTOLIC,
                 PatientDataFrameKey.MSD_ALL_DIASTOLIC,
                 PatientDataFrameKey.MSD_DAY_DIASTOLIC, PatientDataFrameKey.MSD_ALT_DAY_DIASTOLIC,
                 PatientDataFrameKey.MSD_NIGHT_DIASTOLIC, PatientDataFrameKey.MSD_ALT_NIGHT_DIASTOLIC)
    _MEASUREMENT_KEYS = (PatientDataFrameKey.SYSTOLIC, PatientDataFrameKey.DIASTOLIC,
                         PatientDataFrameKey.HEART_RATE)

    _DATE_FORMAT = "%d.%m.%Y"
    _TIME_FORMAT = "%H:%M"
    _DATETIME_FORMAT = "%s %s" % (_DATE_FORMAT, _TIME_FORMAT)

    _TIME_INTERVAL = TimeDelta(minutes=15)
    _START_TIME = datetime.strptime("01.01.1970 8:00", _DATETIME_FORMAT)
    _FINISH_TIME = datetime.strptime("02.01.1970 17:00", _DATETIME_FORMAT) + _TIME_INTERVAL
    _TIME_PERIOD = _FINISH_TIME - _START_TIME
    _FIRST_DAY_START_TIME = datetime.strptime("01.01.1970 7:00", _DATETIME_FORMAT)
    _FIRST_NIGHT_START_TIME = datetime.strptime("01.01.1970 23:00", _DATETIME_FORMAT)
    _ALT_FIRST_DAY_START_TIME = datetime.strptime("01.01.1970 10:00", _DATETIME_FORMAT)
    _ALT_FIRST_DAY_FINISH_TIME = datetime.strptime("01.01.1970 20:00", _DATETIME_FORMAT)
    _ALT_FIRST_NIGHT_START_TIME = datetime.strptime("02.01.1970 00:00", _DATETIME_FORMAT)
    _ALT_FIRST_NIGHT_END_TIME = datetime.strptime("02.01.1970 06:00", _DATETIME_FORMAT)
    _DAY_LEN = _FIRST_NIGHT_START_TIME - _FIRST_DAY_START_TIME
    _NIGHT_LEN = _FIRST_DAY_START_TIME + _TIME_PERIOD - _FIRST_NIGHT_START_TIME
    _TIME_INTERVAL_NUM = int(_TIME_PERIOD / _TIME_INTERVAL)

    def __new__(cls, *args, **kwargs):
        cls.DAY_NIGHT_INTERVALS = cls._calc_day_night_intervals()
        cls.DAY_NIGHT_ALT_INTERVALS = cls._calc_day_night_alt_intervals()
        return super(PatientDataFrame, cls).__new__(cls)

    def __init__(self, patients: Iterable[Patient]):
        self.__columns = PatientDataFrame._prepare_columns()
        data = []
        for patient in patients:
            data.append(PatientDataFrame._prepare_data(patient))
        self.__frame = DataFrame(np.asarray(data), columns=self.__columns)

    @classmethod
    def inc_counter(cls):
        cls._saves_counter += 1

    @staticmethod
    def _prepare_data(patient: Patient):
        measure_keys = (ReportItemKey.SYSTOLIC, ReportItemKey.DIASTOLIC, ReportItemKey.HEART_RATE)
        # noinspection PyListCreation
        data = []
        data.append(patient.id)
        data.append(patient.name)
        data.append(patient.date_of_birth)
        phenotype = patient.blood_pressure_phenotype
        if phenotype:
            data.append(phenotype)
        else:
            data.append(EMPTY_VALUE_STR)
        profile = patient.blood_pressure_profile
        if profile:
            data.append(profile)
        else:
            data.append(EMPTY_VALUE_STR)
        last_hour_max_systolic_blood_pressure = patient.last_hour_max_systolic_blood_pressure
        if last_hour_max_systolic_blood_pressure:
            data.append(last_hour_max_systolic_blood_pressure)
        else:
            data.append(EMPTY_VALUE_STR)
        data.append(patient.avg_systolic_blood_pressure_per_day)
        data.append(patient.avg_diastolic_blood_pressure_per_day)
        data.append(patient.avg_heart_rate_per_day)
        data.append(patient.avg_systolic_blood_pressure_while_awake)
        data.append(patient.avg_diastolic_blood_pressure_while_awake)
        data.append(patient.avg_heart_rate_while_awake)
        data.append(patient.avg_systolic_blood_pressure_while_asleep)
        data.append(patient.avg_diastolic_blood_pressure_while_asleep)
        data.append(patient.avg_heart_rate_while_asleep)
        data.append(patient.first_hour_of_white_coat_window_systolic_blood_pressure)
        time_columns = []
        curr_time = PatientDataFrame._START_TIME
        for i in range(PatientDataFrame._TIME_INTERVAL_NUM):
            time_columns.append(curr_time.time())
            curr_time += PatientDataFrame._TIME_INTERVAL
        index = 0
        measure_times = patient.measures_datetimes
        measure_times_num = len(measure_times)
        sys_all = []
        dia_all = []
        for time in time_columns:
            if index < measure_times_num:
                report_time = measure_times[index].time()
            else:
                report_time = None
            if report_time == time:
                systolic_blood_pressures = patient.systolic_blood_pressures
                diastolic_blood_pressures = patient.diastolic_blood_pressures
                heart_rates = patient.heart_rates
                sys_all.append(systolic_blood_pressures[index])
                dia_all.append(diastolic_blood_pressures[index])
                data.append(systolic_blood_pressures[index])
                data.append(diastolic_blood_pressures[index])
                data.append(heart_rates[index])
                index += 1
            else:
                sys_all.append(None)
                dia_all.append(None)
                for _ in measure_keys:
                    data.append("")
        sys_all = Block[int](sys_all)
        dia_all = Block[int](dia_all)
        # noinspection PyUnresolvedReferences
        dn_intervals = [v for k, v in PatientDataFrame.DAY_NIGHT_INTERVALS]
        # noinspection PyUnresolvedReferences
        dna_intervals = [v for k, v in PatientDataFrame.DAY_NIGHT_ALT_INTERVALS]
        sys_intervals = sys_all.divide_into_parts(dn_intervals)
        dia_intervals = dia_all.divide_into_parts(dn_intervals)
        sysa_intervals = sys_all.divide_into_parts(dna_intervals)
        diaa_intervals = dia_all.divide_into_parts(dna_intervals)
        sys_all = list(sys_all.filter_excluding_items((None, "")))
        dia_all = list(dia_all.filter_excluding_items((None, "")))
        sys_intervals = [list(Block[int](lst).filter_excluding_items((None, "")))
                         for lst in sys_intervals]
        dia_intervals = [list(Block[int](lst).filter_excluding_items((None, "")))
                         for lst in dia_intervals]
        sysa_intervals = [list(Block[int](lst).filter_excluding_items((None, "")))
                          for lst in sysa_intervals][1::2]
        diaa_intervals = [list(Block[int](lst).filter_excluding_items((None, "")))
                          for lst in diaa_intervals][1::2]
        data.append(mutil.msd(sys_all))
        data.append(mutil.msd(sys_intervals[0] + sys_intervals[2]))
        data.append(mutil.msd(sysa_intervals[0] + sysa_intervals[2]))
        data.append(mutil.msd(sys_intervals[1]))
        data.append(mutil.msd(sysa_intervals[1]))
        data.append(mutil.msd(dia_all))
        data.append(mutil.msd(dia_intervals[0] + dia_intervals[2]))
        data.append(mutil.msd(diaa_intervals[0] + diaa_intervals[2]))
        data.append(mutil.msd(dia_intervals[1]))
        data.append(mutil.msd(diaa_intervals[1]))
        return data

    @staticmethod
    def _calc_day_night_intervals():
        twenty_four_hours = TimeDelta(hours=24)
        intervals = []
        first_day_length = PatientDataFrame._FIRST_NIGHT_START_TIME - PatientDataFrame._START_TIME
        intervals.append((PatientDataFrameKey.DAY_TIME.as_string(),
                          int(first_day_length / PatientDataFrame._TIME_INTERVAL)))
        sec_day_start_time = PatientDataFrame._FIRST_DAY_START_TIME + twenty_four_hours
        first_night_length = sec_day_start_time - PatientDataFrame._FIRST_NIGHT_START_TIME
        intervals.append((PatientDataFrameKey.NIGHT_TIME.as_string(),
                          int(first_night_length / PatientDataFrame._TIME_INTERVAL)))
        sec_day_length = PatientDataFrame._FINISH_TIME - sec_day_start_time
        intervals.append((PatientDataFrameKey.DAY_TIME.as_string(),
                          int(sec_day_length / PatientDataFrame._TIME_INTERVAL)))
        return intervals

    @staticmethod
    def _calc_day_night_alt_intervals():
        twenty_four_hours = TimeDelta(hours=24)
        intervals = []
        extra_length = PatientDataFrame._ALT_FIRST_DAY_START_TIME - PatientDataFrame._START_TIME
        intervals.append((PatientDataFrameKey.EXTRA_TIME.as_string(),
                          int(extra_length / PatientDataFrame._TIME_INTERVAL)))
        first_day_length = (PatientDataFrame._ALT_FIRST_DAY_FINISH_TIME -
                            PatientDataFrame._ALT_FIRST_DAY_START_TIME)
        intervals.append((PatientDataFrameKey.DAY_TIME.as_string(),
                          int(first_day_length / PatientDataFrame._TIME_INTERVAL)))
        extra_length = (PatientDataFrame._ALT_FIRST_NIGHT_START_TIME -
                        PatientDataFrame._ALT_FIRST_DAY_FINISH_TIME)
        intervals.append((PatientDataFrameKey.EXTRA_TIME.as_string(),
                          int(extra_length / PatientDataFrame._TIME_INTERVAL)))
        first_night_length = (PatientDataFrame._ALT_FIRST_NIGHT_END_TIME -
                              PatientDataFrame._ALT_FIRST_NIGHT_START_TIME)
        intervals.append((PatientDataFrameKey.NIGHT_TIME.as_string(),
                          int(first_night_length / PatientDataFrame._TIME_INTERVAL)))
        sec_day_start_time = PatientDataFrame._ALT_FIRST_DAY_START_TIME + twenty_four_hours
        extra_length = sec_day_start_time - PatientDataFrame._ALT_FIRST_NIGHT_END_TIME
        intervals.append((PatientDataFrameKey.EXTRA_TIME.as_string(),
                          int(extra_length / PatientDataFrame._TIME_INTERVAL)))
        sec_day_length = PatientDataFrame._FINISH_TIME - sec_day_start_time
        intervals.append((PatientDataFrameKey.DAY_TIME.as_string(),
                          int(sec_day_length / PatientDataFrame._TIME_INTERVAL)))
        return intervals

    @staticmethod
    def _prepare_columns():

        header_rows = []

        header_row = []
        for key in PatientDataFrame._SINGLE_KEYS:
            header_row.append(key.as_string())
        for key in PatientDataFrame._AVG_KEYS:
            for _ in PatientDataFrame._MEASUREMENT_KEYS:
                header_row.append(key.as_string())
        header_row.append(PatientDataFrameKey.FIRST_HOUR_MAX_KEY.as_string())
        # noinspection PyUnresolvedReferences
        for day_night_key, num in PatientDataFrame.DAY_NIGHT_INTERVALS:
            for i in range(num):
                for _ in PatientDataFrame._MEASUREMENT_KEYS:
                    header_row.append(day_night_key)
        for msd_key in PatientDataFrame._MSD_KEYS:
            header_row.append(msd_key.as_string())
        header_rows.append(header_row)

        header_row = []
        for _ in PatientDataFrame._SINGLE_KEYS:
            header_row.append("")
        for _ in PatientDataFrame._AVG_KEYS:
            for key in PatientDataFrame._MEASUREMENT_KEYS:
                header_row.append(key.as_string())
        header_row.append("")
        time_columns = []
        curr_time = PatientDataFrame._START_TIME
        for i in range(PatientDataFrame._TIME_INTERVAL_NUM):
            time_columns.append('%s' % curr_time.time().strftime(PatientDataFrame._TIME_FORMAT))
            curr_time += PatientDataFrame._TIME_INTERVAL
        for time_column in time_columns:
            for _ in PatientDataFrame._MEASUREMENT_KEYS:
                header_row.append(time_column)
        for _ in PatientDataFrame._MSD_KEYS:
            header_row.append("")
        header_rows.append(header_row)

        header_row = []
        middle_keys_len = len(PatientDataFrame._SINGLE_KEYS)
        middle_keys_len += len(PatientDataFrame._AVG_KEYS) * len(PatientDataFrame._MEASUREMENT_KEYS)
        middle_keys_len += 1
        for i in range(middle_keys_len):
            header_row.append("")
        for _ in time_columns:
            for key in PatientDataFrame._MEASUREMENT_KEYS:
                header_row.append(key.as_string())
        for _ in PatientDataFrame._MSD_KEYS:
            header_row.append("")
        header_rows.append(header_row)

        return header_rows

    @property
    def frame(self):
        return self.__frame

    def save_csv(self, basic_output_dir: Path, basic_name: str, encoding=None, separator=','):
        while True:
            new_name = "%s_%d" % (basic_name, self._saves_counter)
            output_path = Path(basic_output_dir, "tables")
            paths.create_dir(output_path)
            output_path = Path(output_path, new_name).with_suffix('.' + Extension.CSV.as_string())
            if output_path.is_file():
                self.inc_counter()
                continue
            else:
                self.__frame.to_csv(str(output_path), encoding=encoding, index=False, sep=separator)
                LOGGER.info("The output file was saved as %s" % output_path.absolute())
                break
