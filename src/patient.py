from typing import Union, List
# noinspection PyPep8Naming
from datetime import timedelta as TimeDelta, datetime
from src.report import Report
from src.report_item import ReportItemKey

EMPTY_VALUE_STR = "--"

_BP_AWAKE_SYS_NORM = 135
_DIFF_BP_SYS_NORM = 10


class Patient(object):

    def __init__(self, report: Report):
        self.__report_name = report.name
        self.__id = report.patient_id
        self.__name = report.patient_name
        self.__date_of_birth = report.patient_date_of_birth
        self.__first_hour_of_white_coat_window_systolic_blood_pressure = report.white_coat_window[
            ReportItemKey.SYSTOLIC][ReportItemKey.FIRST_HOUR]
        self.__avg_systolic_blood_pressure_per_day = report.avg_bp[
            ReportItemKey.SYSTOLIC][ReportItemKey.TWENTY_FOUR_HOURS]
        self.__avg_diastolic_blood_pressure_per_day = report.avg_bp[
            ReportItemKey.DIASTOLIC][ReportItemKey.TWENTY_FOUR_HOURS]
        self.__avg_heart_rate_per_day = report.avg_bp[
            ReportItemKey.HEART_RATE][ReportItemKey.TWENTY_FOUR_HOURS]
        self.__avg_systolic_blood_pressure_while_awake = report.avg_bp[
            ReportItemKey.SYSTOLIC][ReportItemKey.AWAKE]
        self.__avg_diastolic_blood_pressure_while_awake = report.avg_bp[
            ReportItemKey.DIASTOLIC][ReportItemKey.AWAKE]
        self.__avg_heart_rate_while_awake = report.avg_bp[
            ReportItemKey.HEART_RATE][ReportItemKey.AWAKE]
        self.__avg_systolic_blood_pressure_while_asleep = report.avg_bp[
            ReportItemKey.SYSTOLIC][ReportItemKey.ASLEEP]
        self.__avg_diastolic_blood_pressure_while_asleep = report.avg_bp[
            ReportItemKey.DIASTOLIC][ReportItemKey.ASLEEP]
        self.__avg_heart_rate_while_asleep = report.avg_bp[
            ReportItemKey.HEART_RATE][ReportItemKey.ASLEEP]
        values = report.values
        self.__measures_datetimes = values[ReportItemKey.DATETIME]
        self.__systolic_blood_pressures = values[ReportItemKey.SYSTOLIC]
        self.__diastolic_blood_pressures = values[ReportItemKey.DIASTOLIC]
        self.__heart_rates = values[ReportItemKey.HEART_RATE]
        self.__blood_pressure_profile = Patient._calc_blood_pressure_profile(report.night_time_dip)
        self.__blood_pressure_phenotype = Patient._calc_blood_pressure_phenotype(
            report.avg_bp, report.white_coat_window)
        last_hour_max_systolic_blood_pressure = self.__calc_last_hour_max_systolic_blood_pressure()
        self.__last_hour_max_systolic_blood_pressure = last_hour_max_systolic_blood_pressure

    @property
    def report_name(self) -> str:
        return self.__report_name

    @property
    def id(self) -> str:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def date_of_birth(self) -> str:
        return self.__date_of_birth

    @property
    def first_hour_of_white_coat_window_systolic_blood_pressure(self):
        return self.__first_hour_of_white_coat_window_systolic_blood_pressure

    @property
    def avg_systolic_blood_pressure_per_day(self):
        return self.__avg_systolic_blood_pressure_per_day

    @property
    def avg_diastolic_blood_pressure_per_day(self):
        return self.__avg_diastolic_blood_pressure_per_day

    @property
    def avg_heart_rate_per_day(self):
        return self.__avg_heart_rate_per_day

    @property
    def avg_systolic_blood_pressure_while_awake(self):
        return self.__avg_systolic_blood_pressure_while_awake

    @property
    def avg_diastolic_blood_pressure_while_awake(self):
        return self.__avg_diastolic_blood_pressure_while_awake

    @property
    def avg_heart_rate_while_awake(self):
        return self.__avg_heart_rate_while_awake

    @property
    def avg_systolic_blood_pressure_while_asleep(self):
        return self.__avg_systolic_blood_pressure_while_asleep

    @property
    def avg_diastolic_blood_pressure_while_asleep(self):
        return self.__avg_diastolic_blood_pressure_while_asleep

    @property
    def avg_heart_rate_while_asleep(self):
        return self.__avg_heart_rate_while_asleep

    @property
    def blood_pressure_profile(self) -> int:
        return self.__blood_pressure_profile

    @property
    def blood_pressure_phenotype(self) -> int:
        return self.__blood_pressure_phenotype

    @property
    def last_hour_max_systolic_blood_pressure(self) -> Union[None, int]:
        return self.__last_hour_max_systolic_blood_pressure

    @property
    def measures_datetimes(self) -> List[datetime]:
        return self.__measures_datetimes

    @property
    def systolic_blood_pressures(self) -> List[Union[str, int]]:
        return self.__systolic_blood_pressures

    @property
    def diastolic_blood_pressures(self) -> List[Union[str, int]]:
        return self.__diastolic_blood_pressures

    @property
    def heart_rates(self) -> List[Union[str, int]]:
        return self.__heart_rates

    def __calc_last_hour_max_systolic_blood_pressure(self) -> Union[None, int]:
        last_index = len(self.measures_datetimes) - 1
        last_hour = self.measures_datetimes[-1] - TimeDelta(hours=1)
        last_hour_index = last_index
        for i, time in enumerate(self.measures_datetimes):
            if time >= last_hour:
                last_hour_index = i
        last_hour_systolic_blood_pressures = self.systolic_blood_pressures[
                                             last_hour_index:last_index + 1]
        try:
            if isinstance(last_hour_systolic_blood_pressures, list):
                last_hour_max_systolic_blood_pressure = max(last_hour_systolic_blood_pressures)
            else:
                last_hour_max_systolic_blood_pressure = last_hour_systolic_blood_pressures
        except ValueError:
            return None
        return last_hour_max_systolic_blood_pressure

    @staticmethod
    def _calc_blood_pressure_profile(night_time_dip) -> int:
        ntd_sys = night_time_dip[ReportItemKey.SYSTOLIC][ReportItemKey.DIP]
        if ntd_sys == EMPTY_VALUE_STR:
            return 0
        if 10. < ntd_sys <= 20:
            return 1
        elif 0. < ntd_sys <= 10:
            return 2
        elif ntd_sys <= 0.:
            return 3
        elif 20. < ntd_sys:
            return 4

    @staticmethod
    def _calc_blood_pressure_phenotype(avg_bp, white_coat_window) -> int:
        avg_bp_sys = avg_bp[ReportItemKey.SYSTOLIC]
        avg_bp_sys_awake = avg_bp_sys[ReportItemKey.AWAKE]
        wcw_sys = white_coat_window[ReportItemKey.SYSTOLIC]
        wcw_sys_first_hour = wcw_sys[ReportItemKey.FIRST_HOUR]
        if wcw_sys_first_hour == EMPTY_VALUE_STR:
            return 0
        diff = abs(avg_bp_sys_awake - wcw_sys_first_hour)
        if (avg_bp_sys_awake < _BP_AWAKE_SYS_NORM
            and wcw_sys_first_hour < _BP_AWAKE_SYS_NORM
            and diff < _DIFF_BP_SYS_NORM):
            return 1
        elif (avg_bp_sys_awake < _BP_AWAKE_SYS_NORM and wcw_sys_first_hour < _BP_AWAKE_SYS_NORM
              and diff >= _DIFF_BP_SYS_NORM):
            return 2
        elif ((avg_bp_sys_awake >= _BP_AWAKE_SYS_NORM or wcw_sys_first_hour >= _BP_AWAKE_SYS_NORM)
              and diff < _DIFF_BP_SYS_NORM):
            return 3
        elif (avg_bp_sys_awake >= _BP_AWAKE_SYS_NORM > wcw_sys_first_hour
              and diff >= _DIFF_BP_SYS_NORM):
            return 4
        elif (avg_bp_sys_awake < _BP_AWAKE_SYS_NORM <= wcw_sys_first_hour
              and diff >= _DIFF_BP_SYS_NORM):
            return 5
        elif (avg_bp_sys_awake >= _BP_AWAKE_SYS_NORM
              and wcw_sys_first_hour >= _BP_AWAKE_SYS_NORM
              and diff >= _DIFF_BP_SYS_NORM):
            return 6






