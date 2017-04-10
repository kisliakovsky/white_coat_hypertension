import operator
from collections import defaultdict
from datetime import datetime

from sys import stderr

import collections
from typing import Tuple, Dict, TypeVar, List, Union

from src.file_process import ReportSpace, BlockStore
from src.report_item import ReportItem, ReportItemKey, ReportItemPattern, ReportString, ReportBlock
from src.util import math_util as mutil


class Report(object):

    _PERIOD_ITEMS = ReportItem.PERIOD_TIME, ReportItem.PERIOD_INTERVAL
    _VALUES_ITEMS = ReportItem.SYSTOLIC, ReportItem.DIASTOLIC, ReportItem.HEART_RATE
    _DAY_NIGHT_KEYS = ReportItemKey.DAY, ReportItemKey.NIGHT
    _READINGS_PAIR = ReportItemPattern.READINGS, (ReportItem.TOTAL_READINGS,
                                                  ReportItem.SUCCESSFUL_READINGS)
    _VALUES_KEYS = ReportItemKey.SYSTOLIC, ReportItemKey.DIASTOLIC, ReportItemKey.HEART_RATE
    _AVG_COL_KEYS = ReportItemKey.SYSTOLIC, ReportItemKey.DIASTOLIC, ReportItemKey.HEART_RATE
    _AVG_ROW_KEYS = ReportItemKey.TWENTY_FOUR_HOURS, ReportItemKey.AWAKE, ReportItemKey.ASLEEP
    _WHITE_COAT_WINDOW_KEYS = ReportItemKey.READINGS, ReportItemKey.FIRST_HOUR

    _DATE_FORMAT = "%d.%m.%Y"
    _TIME_FORMAT = "%H:%M"
    _DATE_TIME_FORMAT = "%s %s" % (_DATE_FORMAT, _TIME_FORMAT)

    _VALUES_SD_KEYS = (ReportSpace.VALUES_1_COLUMN_SD, ReportSpace.VALUES_2_COLUMN_SD,
                       ReportSpace.VALUES_3_COLUMN_SD, ReportSpace.VALUES_4_COLUMN_SD)
    _VALUES_HR_KEYS = (ReportSpace.VALUES_1_COLUMN_HR, ReportSpace.VALUES_2_COLUMN_HR,
                       ReportSpace.VALUES_3_COLUMN_HR, ReportSpace.VALUES_4_COLUMN_HR)

    _MAX_COLUMN_VALUES_NUM = 25

    def __init__(self, name: str, blocks: BlockStore):
        self.__name = name
        self.__blocks = blocks
        main_block = blocks.get(ReportSpace.ALL)
        main_block.remove_item(ReportItemPattern.PAGINATOR)
        self.__title = self.__parse_title()
        self.__physician = self.__parse_physician()
        self.__period = self.__parse_period()
        self.__study_date = self.__parse_study_date()
        self.__awake, self.__asleep = self.__parse_awake_asleep
        self.__bp_threshold = self.__parse_bp_threshold()
        self.__readings = self.__parse_readings()
        self.__bp_load = self.__parse_bp_load()
        main_block.remove_item(ReportItemPattern.PERIOD)
        self.__patient_id = self.__parse_patient_id()
        self.__patient_name = self.__parse_patient_name()
        sex_and_age_and_dob = self.__parse_sex_age_dob_triplet()
        self.__patient_sex, self.__patient_age, self.__patient_date_of_birth = sex_and_age_and_dob
        self.__avg_bp = self.__parse_avg_bp()
        self.__white_coat_window = self.__parse_white_coat_window()
        self.__night_time_dip = self.__parse_night_time_dip()
        self.__values, self.__success, self.__message = self.__parse_values()

    @property
    def name(self) -> str:
        return self.__name

    @property
    def blocks(self) -> BlockStore:
        return self.__blocks

    @property
    def title(self) -> str:
        return self.__title

    @property
    def physician(self) -> str:
        return self.__physician

    @property
    def period(self) -> Dict[ReportItemKey, Dict[ReportItemKey, str]]:
        return self.__period

    @property
    def study_date(self) -> str:
        return self.__study_date

    @property
    def awake(self) -> str:
        return self.__awake

    @property
    def asleep(self) -> str:
        return self.__asleep

    @property
    def bp_threshold(self) -> Dict[ReportItemKey, str]:
        return self.__bp_threshold

    @property
    def readings(self) -> Dict[ReportItemKey, str]:
        return self.__readings

    @property
    def bp_load(self) -> Dict[ReportItemKey, str]:
        return self.__bp_load

    @property
    def patient_id(self) -> str:
        return self.__patient_id

    @property
    def patient_name(self) -> str:
        return self.__patient_name

    @property
    def patient_sex(self) -> str:
        return self.__patient_sex

    @property
    def patient_age(self) -> str:
        return self.__patient_age

    @property
    def patient_date_of_birth(self) -> str:
        return self.__patient_date_of_birth

    @property
    def values(self) -> Dict[ReportItemKey, List[Union[str, int, datetime]]]:
        return self.__values

    @property
    def avg_bp(self) -> Dict[ReportItemKey, Dict[ReportItemKey, Union[str, int]]]:
        return self.__avg_bp

    @property
    def night_time_dip(self) -> Dict[ReportItemKey, Dict[ReportItemKey, Union[str, float]]]:
        return self.__night_time_dip

    @property
    def white_coat_window(self) -> Dict[ReportItemKey, Dict[ReportItemKey, Union[str, int]]]:
        return self.__white_coat_window

    @property
    def success(self) -> bool:
        return self.__success

    @property
    def message(self) -> str:
        return self.__message

    def __parse_title(self) -> str:
        main_block = self.blocks.get(ReportSpace.ALL)
        title = main_block.remove_item(ReportItemPattern.TITLE)
        return str(title)

    def __parse_physician(self) -> str:
        main_block = self.blocks.get(ReportSpace.ALL)
        physician_entry = main_block.remove_item(ReportItemPattern.PHYSICIAN_ENTRY).as_entry()
        physician = physician_entry[1]
        return physician

    def __parse_study_date(self) -> str:
        main_block = self.blocks.get(ReportSpace.ALL)
        study_date = main_block.remove_item(ReportItemPattern.STUDY_DATE)
        study_date = study_date.matches(ReportItemPattern.DATE)
        return study_date

    def __parse_patient_id(self) -> str:
        main_block = self.blocks.get(ReportSpace.ALL)
        patient_block = self.blocks.get(ReportSpace.PATIENT)
        patient_id = str(patient_block.remove_item(ReportItemPattern.PATIENT_ID))
        if not patient_id:
            patient_id = str(main_block.remove_item(ReportItemPattern.PATIENT_ID))
        return "'%s'" % patient_id

    def __parse_patient_name(self) -> str:
        main_block = self.blocks.get(ReportSpace.ALL)
        patient_block = self.blocks.get(ReportSpace.PATIENT)
        patient_name = str(patient_block.remove_item(ReportItemPattern.PATIENT_NAME))
        if not patient_name:
            patient_name = str(main_block.remove_item(ReportItemPattern.PATIENT_NAME))
        return patient_name

    def __parse_period(self) -> Dict[ReportItemKey, Dict[ReportItemKey, str]]:
        day_night_block = self.blocks.get(ReportSpace.DAY_NIGHT)
        day_night_block.remove_item(ReportItemPattern.PERIOD)
        num_of_values = 2
        period_times = day_night_block.search_sequence_by_header_pattern_and_remove(
            ReportItem.PERIOD_TIME.pattern, num_of_values)
        period_intervals = day_night_block.search_sequence_by_header_pattern_and_remove(
            ReportItem.PERIOD_INTERVAL.pattern, num_of_values)
        period = {}
        if period_times and period_intervals:
            for i, key in enumerate(Report._DAY_NIGHT_KEYS):
                period_time = period_times[i]
                period_interval = ReportString(period_intervals[i]).as_value()
                period[key] = {ReportItem.PERIOD_TIME.key: period_time,
                               ReportItem.PERIOD_INTERVAL.key: period_interval}
        return period

    @property
    def __parse_awake_asleep(self) -> Tuple[str, str]:
        day_night_block = self.blocks.get(ReportSpace.DAY_NIGHT)
        awake = None
        asleep = None
        num_of_values = 2
        awake_asleep = day_night_block.search_sequence_by_header_pattern_and_remove(
            ReportItemPattern.AWAKE_ASLEEP, num_of_values)
        if awake_asleep:
            awake = ReportString(awake_asleep[0]).as_entry()
            asleep = ReportString(awake_asleep[1]).as_entry()
        return awake[1], asleep[1]

    def __parse_readings(self) -> Dict[ReportItemKey, str]:
        readings = {}
        main_block = self.blocks.get(ReportSpace.ALL)
        readings_block = self.blocks.get(ReportSpace.READINGS_BP)
        # TODO: Why is it removed from the main block not from the readings block?
        main_block.remove_item(ReportItemPattern.READINGS)
        total_readings = readings_block.remove_item(ReportItemPattern.TOTAL_READINGS)
        total_readings = total_readings.as_entry()
        readings[ReportItemKey.TOTAL_READINGS] = total_readings[1]
        successful_readings = readings_block.remove_item(ReportItemPattern.SUCCESSFUL_READINGS)
        readings[ReportItemKey.SUCCESSFUL_READINGS] = str(successful_readings)
        return readings

    def __parse_bp_threshold(self) -> Dict[ReportItemKey, str]:
        bp_value = {}
        num_of_values = 2
        day_night_block = self.blocks.get(ReportSpace.DAY_NIGHT)
        thresholds = day_night_block.search_sequence_by_header_pattern_and_remove(
            ReportItemPattern.BLOOD_PRESSURE_THRESHOLD, num_of_values)
        if thresholds:
            for i, key in enumerate(Report._DAY_NIGHT_KEYS):
                threshold = ReportString(thresholds[i]).as_entry()
                bp_value[key] = ReportString(threshold[1]).as_value()
        return bp_value

    def __parse_bp_load(self) -> Dict[ReportItemKey, str]:
        bp_value = {}
        num_of_values = 2
        day_night_block = self.blocks.get(ReportSpace.READINGS_BP)
        loads = day_night_block.search_sequence_by_header_pattern_and_remove(
            ReportItemPattern.BLOOD_PRESSURE_LOAD, num_of_values)
        if loads:
            for i, key in enumerate(Report._DAY_NIGHT_KEYS):
                load = ReportString(loads[i])
                key_str = key.as_string()
                if load.case_insensitive().starts_with(key_str):
                    load = load.cut_header(len(key_str))
                bp_value[key] = str(load)
        return bp_value

    def __parse_sex_age_dob_triplet(self) -> Tuple[str, str, str]:
        num_of_values = 2
        patient_block = self.blocks.get(ReportSpace.PATIENT)
        patient_sex, age_and_birth_date = patient_block.search_sequence_by_header_pattern(
            ReportItemPattern.PATIENT_SEX, num_of_values)
        patient_age = None
        patient_date_of_birth = None
        if age_and_birth_date:
            patient_age = age_and_birth_date[0]
            # TODO: Try to refactor it.
            try:
                patient_date_of_birth = age_and_birth_date[1]
                num_of_values = 2
                patient_block.search_sequence_by_header_pattern_and_remove(
                    ReportItemPattern.PATIENT_SEX, num_of_values)
            except ValueError:
                pass
        return patient_sex, patient_age, patient_date_of_birth

    # TODO: Try to refactor it.
    def __parse_avg_bp_24h_row(self) -> List[int]:
        row = []
        key_index_pairs = []
        avg_bp_block = self.blocks.get(ReportSpace.AVG_BP)
        for value_item in Report._VALUES_ITEMS:
            index, _ = avg_bp_block.search_first_occurrence_by_pattern(value_item.pattern)
            key_index_pairs.append((value_item.key, index))
        key_index_pairs.sort(key=operator.itemgetter(1))
        val_dict = {}
        remove_shift = 2
        for i, key_index_pair in enumerate(key_index_pairs):
            key, index = key_index_pair
            avg_br_fr_val = avg_bp_block.search_among_neighbors_and_remove(
                index - remove_shift * i, ReportItemPattern.TWO_THREE_DIGITS_NUM)
            val_dict[key] = str(avg_br_fr_val)
        for value_key in Report._VALUES_KEYS:
            row.append(int(val_dict[value_key]))
        avg_bp_block.remove_item(ReportItemPattern.TWENTY_FOUR_HOURS)
        return row

    # TODO: Try to refactor it.
    def __parse_avg_bp(self) -> Dict[ReportItemKey, Dict[ReportItemKey, Union[str, int]]]:
        avg_bp = defaultdict(dict)
        avg_bp_block = self.blocks.get(ReportSpace.AVG_BP)
        avg_bp_block.remove_item(ReportItemPattern.AVG_BLOOD_PRESSURE)
        for i in range(9):
            avg_bp_block.remove_item(ReportItemPattern.PARENTHESES_NUM)
        twenty_four_hours_values = self.__parse_avg_bp_24h_row()
        num_of_values = 3

        def parse_avg_seq_vals(pattern: ReportItemPattern) -> List[Union[str, int]]:
            values = avg_bp_block.search_sequence_by_header_pattern_and_remove(pattern,
                                                                               num_of_values)
            for k in range(len(values)):
                try:
                    values[k] = int(values[k])
                except ValueError:
                    pass
            return values

        awake_values = parse_avg_seq_vals(ReportItemPattern.AWAKE)
        asleep_values = parse_avg_seq_vals(ReportItemPattern.ASLEEP)
        all_values = (twenty_four_hours_values, awake_values, asleep_values)
        for i, row in enumerate(all_values):
            for j, val in enumerate(row):
                avg_bp[Report._AVG_COL_KEYS[j]][Report._AVG_ROW_KEYS[i]] = val
        return dict(avg_bp)

    # TODO: Try to refactor it.
    def __parse_white_coat_window(self) -> Dict[ReportItemKey, Dict[ReportItemKey,
                                                                    Union[str, int]]]:
        white_coat_window = defaultdict(dict)
        white_coat_window_block = self.blocks.get(ReportSpace.WHITE_COAT_WINDOW)
        white_coat_window_block.remove_item(ReportItemPattern.WHITE_COAT_WINDOW)
        white_coat_window_block.remove_item(ReportItemPattern.NIGHT_TIME_DIP)
        white_coat_window_block.remove_item(ReportItemPattern.READINGS)
        white_coat_window_block.remove_item(ReportItemPattern.FIRST_HOUR)
        num_of_values = 2

        def parse_white_coat_window_consecutive_values(
                pattern: ReportItemPattern) -> List[Union[str, int]]:
            values = white_coat_window_block.search_sequence_by_header_pattern_and_remove(
                pattern, num_of_values)
            for k in range(len(values)):
                try:
                    values[k] = int(values[k])
                except ValueError:
                    pass
            return values

        sys_values = parse_white_coat_window_consecutive_values(Report._VALUES_ITEMS[0].pattern)
        dia_values = parse_white_coat_window_consecutive_values(Report._VALUES_ITEMS[1].pattern)
        hr_values = parse_white_coat_window_consecutive_values(Report._VALUES_ITEMS[2].pattern)
        all_values = [sys_values, dia_values, hr_values]
        for i, row in enumerate(all_values):
            for j, value in enumerate(row):
                values_by_type = white_coat_window[Report._VALUES_ITEMS[i].key]
                values_by_type[Report._WHITE_COAT_WINDOW_KEYS[j]] = value
        return dict(white_coat_window)

    def __parse_night_time_dip(self) -> Dict[ReportItemKey, Dict[ReportItemKey, Union[str, float]]]:
        night_time_dip = defaultdict(dict)
        night_time_dip_block = self.blocks.get(ReportSpace.NIGHT_TIME_DIP)
        night_time_dip_block.remove_item(ReportItemPattern.NIGHT_TIME_DIP)
        num_of_values = 1

        def parse_night_time_dip_value(
                pattern: ReportItemPattern) -> Union[str, float]:
            values = night_time_dip_block.search_sequence_by_header_pattern_and_remove(
                pattern, num_of_values)
            corrected_by_delimiter_value = values[0].replace(',', '.')
            try:
                corrected_by_delimiter_value = float(corrected_by_delimiter_value)
            except ValueError:
                pass
            return corrected_by_delimiter_value

        for i in range(2):
            value_item = Report._VALUES_ITEMS[i]
            values_by_type = night_time_dip[value_item.key]
            values_by_type[ReportItemKey.DIP] = parse_night_time_dip_value(value_item.pattern)
        return dict(night_time_dip)

    def __parse_values(self) -> Tuple[Dict[ReportItemKey, List[Union[str, int, datetime]]],
                                      bool, str]:
        all_vals = {}
        dt_cols, t_nums = self.__parse_datetime_columns(remove_after=True)
        hr_cols = self.__parse_hr_columns(t_nums)
        sd_cols, (success, message) = self.__parse_sd_columns(t_nums)
        sys_cols, dia_cols = sd_cols
        for _ in t_nums:
            all_vals[ReportItemKey.DATETIME] = [item for sublist in dt_cols for item in sublist]
            all_vals[ReportItemKey.SYSTOLIC] = [item for sublist in sys_cols for item in sublist]
            all_vals[ReportItemKey.DIASTOLIC] = [item for sublist in dia_cols for item in sublist]
            all_vals[ReportItemKey.HEART_RATE] = [item for sublist in hr_cols for item in sublist]
        return all_vals, success, message

    def __parse_sd_columns(
            self, t_nums:
            List[Union[Tuple[int, ...], int, str]]) -> Tuple[Tuple[List[List[Union[int, str]]],
                                                                   List[List[Union[int, str]]]],
                                                             Tuple[bool, str]]:
        sys_cols = []
        dia_cols = []
        message = None
        global_success = True
        for i, t_num in enumerate(t_nums):
            res, local_success = self.__parse_sd_column(Report._VALUES_SD_KEYS[i], t_num)
            if not local_success:
                global_success = local_success
                message = "Please enter the values of periodic measurements of " \
                          "the blood pressure (systolic and diastolic) of the column #%d " \
                          "manually" % (i + 1)
            sys_col, dia_col = res
            if sys_col:
                sys_cols.append(sys_col)
            if dia_col:
                dia_cols.append(dia_col)
        return (sys_cols, dia_cols), (global_success, message)

    def __parse_sd_column(
            self, sd_key: ReportSpace, t_num: Union[Tuple[int, ...],
                                                    int]) -> Union[
                                                             Tuple[Tuple[List[int], ...], bool],
                                                             Tuple[List[int], List[int]]]:
        sys_column = []
        dia_column = []
        sd_col = []
        num_group = []
        block = self.blocks.get(sd_key)
        if not block:
            return sys_column, dia_column
        index, _ = block.search_first_occurrence_by_pattern(ReportItemPattern.TWO_THREE_DIGITS_NUM)
        while index < len(block):
            value = block[index]
            match = ReportString(value).matches(ReportItemPattern.TWO_THREE_DIGITS_NUM)
            if match:
                num_group.append(int(value))
            elif num_group:
                sd_col.append(num_group)
                num_group = []
            index += 1
        if num_group:
            sd_col.append(num_group)
        col_pair = None

        def distribute_columns_by_mean(columns: List[List[int]]):
            if mutil.mean(columns[0]) < mutil.mean(columns[1]):
                columns[0], columns[1] = columns[1], columns[0]

        def merge_columns(col_first_part, col_second_part):
            columns = [col_first_part[0] + col_second_part[0],
                       col_first_part[1] + col_second_part[1]]
            return columns

        def distribute_and_merge_columns(col_first_part, col_second_part):
            distribute_columns_by_mean(col_first_part)
            distribute_columns_by_mean(col_second_part)
            return merge_columns(col_first_part, col_second_part)

        def process_columns(columns: List[Tuple[int, List[int]]]):
            columns = columns[:2]
            return [each[0] for each in columns], [each[1] for each in columns]

        def process_double_columns(columns):
            k, columns = columns[0]
            half_len = int(len(columns) / 2)
            return k, [columns[:half_len], columns[half_len:]]

        def clear_values(indices: List[int]):
            for idx in sorted(indices, reverse=True):
                del sd_col[idx]

        if isinstance(t_num, tuple):
            tn_full = sum(t_num)
            if len(t_num) == 2:
                tn_fp, tn_sp = t_num
                double_tn_fp, double_tn_sp = tuple([2 * each for each in t_num])
                sd_fp, sd_sp = [], []
                double_sd_fp, double_sd_sp = [], []
                sd_full = []
                for j, value in enumerate(sd_col):
                    val_len = len(value)
                    if val_len == tn_fp:
                        sd_fp.append((j, value))
                    elif val_len == tn_sp:
                        sd_sp.append((j, value))
                    elif double_tn_fp != double_tn_sp:
                        if val_len == double_tn_fp:
                            double_sd_fp.append((j, value))
                        elif val_len == double_tn_sp:
                            double_sd_sp.append((j, value))
                        elif val_len == tn_full:
                            sd_full.append((j, value))
                    elif val_len == tn_full:
                        sd_full.append((j, value))
                sd_fp_len = len(sd_fp)
                sd_sp_len = len(sd_sp)
                double_sd_fp_len = len(double_sd_fp)
                double_sd_sp_len = len(double_sd_sp)
                sd_full_len = len(sd_full)
                remove_indices = []
                if sd_fp_len >= 2:
                    indcs, sd_fp = process_columns(sd_fp)
                    remove_indices.extend(indcs)
                    if sd_sp_len >= 2:
                        indcs, sd_sp = process_columns(sd_sp)
                        remove_indices.extend(indcs)
                        col_pair = distribute_and_merge_columns(sd_fp, sd_sp)
                        clear_values(remove_indices)
                    elif double_sd_sp_len >= 1:
                        index, double_sd_sp = process_double_columns(double_sd_sp)
                        remove_indices.append(index)
                        col_pair = distribute_and_merge_columns(sd_fp, double_sd_sp)
                        clear_values(remove_indices)
                    elif sd_full_len >= 1:
                        indcs, sd_full = process_columns(sd_full)
                        col_pair = [sd_fp[0] + sd_fp[1], sd_full[0]]
                        distribute_columns_by_mean(col_pair)
                        clear_values(indcs)
                elif double_sd_fp_len >= 1:
                    index, double_sd_fp = process_double_columns(double_sd_fp)
                    remove_indices.append(index)
                    if sd_sp_len >= 2:
                        indcs, sd_sp = process_columns(sd_sp)
                        remove_indices.extend(indcs)
                        col_pair = distribute_and_merge_columns(double_sd_fp, sd_sp)
                        clear_values(remove_indices)
                    elif double_sd_sp_len >= 1:
                        index, double_sd_sp = process_double_columns(double_sd_sp)
                        remove_indices.append(index)
                        col_pair = distribute_and_merge_columns(double_sd_fp, double_sd_sp)
                        clear_values(remove_indices)
                elif sd_fp_len >= 1 and sd_sp_len >= 1 and sd_full_len >= 1:
                    indcs, sd_fp = process_columns(sd_fp)
                    remove_indices.extend(indcs)
                    indcs, sd_sp = process_columns(sd_sp)
                    remove_indices.extend(indcs)
                    indcs, sd_full = process_columns(sd_full)
                    col_pair = [sd_fp[0] + sd_sp[0], sd_full[0]]
                    distribute_columns_by_mean(col_pair)
                    clear_values(indcs)
                if sd_full_len >= 2:
                    indcs, sd_full = process_columns(sd_full)
                    distribute_columns_by_mean(sd_full)
                    col_pair = sd_full
                    clear_values(indcs)
            if not col_pair:
                col_pair = []
                for _ in range(2):
                    # noinspection PyUnusedLocal
                    col_pair.append(['' for temp in range(tn_full)])
                return tuple(col_pair), False
        else:
            pair = []
            for j, value in enumerate(sd_col):
                val_len = len(value)
                double_time_num = t_num * 2
                if val_len == t_num:
                    pair.append((j, value))
                    if len(pair) == 2:
                        indcs, pair = process_columns(pair)
                        distribute_columns_by_mean(pair)
                        col_pair = pair
                        clear_values(indcs)
                        break
                elif val_len == double_time_num:
                    _, double_col = process_double_columns([(j, value)])
                    distribute_columns_by_mean(double_col)
                    col_pair = double_col
                    clear_values([j])
                    break
        return tuple(col_pair), True

    def __parse_hr_columns(self, t_nums):
        hr_columns = []
        for i, t_num in enumerate(t_nums):
            hr_column = self.__parse_hr_column(Report._VALUES_HR_KEYS[i], t_num)
            if hr_column:
                hr_columns.append(hr_column)
        return hr_columns

    def __parse_hr_column(self, hr_key: ReportSpace, t_num):
        hr_column = []
        num_group = []
        block = self.blocks.get(hr_key)
        if not block:
            return hr_column
        index, _ = block.search_first_occurrence_by_pattern(ReportItemPattern.TWO_THREE_DIGITS_NUM)
        while index < len(block):
            value = block[index]
            match = ReportString(value).matches(ReportItemPattern.TWO_THREE_DIGITS_NUM)
            if match:
                num_group.append(int(value))
            elif num_group:
                hr_column.append(num_group)
                num_group = []
            index += 1
        if num_group:
            hr_column.append(num_group)
        if isinstance(t_num, tuple):
            buff = []
            for num in t_num:
                for part in hr_column:
                    if num == len(part):
                        buff.append(part)
                        break
            if len(buff) == len(t_num):
                hr_column = [item for sublist in buff for item in sublist]
            elif len(hr_column[0]) == sum(t_num):
                hr_column = hr_column[0]
            else:
                print("Wrong number of values", file=stderr)
        else:
            if len(hr_column[0]) == t_num:
                hr_column = hr_column[0]
            else:
                print("Wrong number of values", file=stderr)
        return hr_column

    def __parse_datetime_columns(self, remove_after=False):
        datetime_columns = []
        t_nums = []
        date_result = None
        for key in Report._VALUES_SD_KEYS:
            datetime_column, t_num, date_result = self.__parse_datetime_column(key, remove_after,
                                                                               date_result)
            if datetime_column:
                datetime_columns.append(datetime_column)
                t_nums.append(t_num)
        return datetime_columns, t_nums

    def __parse_datetime_column(self, datetime_key: ReportSpace, remove_after=False,
                                date_result=None):
        datetime_column = []
        counter = 0
        times = []
        time_num = []
        block = self.blocks.get(datetime_key)
        if not block:
            return datetime_column, 0, date_result
        if not date_result:
            _, date_result = block.search_first_occurrence_by_pattern(ReportItemPattern.DATE)
            date_result = str(date_result)
        index, time_result = block.search_first_occurrence_by_pattern(ReportItemPattern.TIME)
        while index is not None and index < len(block):
            value = block[index]
            match = ReportString(value).matches(ReportItemPattern.DATE)
            if match:
                datetime_column.extend(times)
                time_num.append(counter)
                date_result = value
                times = []
                counter = 0
            else:
                match = ReportString(value).matches(ReportItemPattern.TIME)
                if match:
                    time_result = value
                    dt = " ".join((date_result, time_result))
                    times.append(datetime.strptime(dt, Report._DATE_TIME_FORMAT))
                    counter += 1
                elif times:
                    datetime_column.extend(times)
                    if len(time_num) > 0 and time_num[0] == 0:
                        time_num[0] = counter
                    else:
                        time_num.append(counter)
                    times = []
                    counter = 0
            index += 1
        if times:
            datetime_column.extend(times)
            time_num.append(counter)
        if len(time_num) == 1:
            time_num = time_num[0]
        else:
            if len(time_num) == 2 and time_num[1] == 0:
                time_num = time_num[0]
            else:
                time_num = tuple(time_num)
        if remove_after:
            new_data = []
            first = False
            if isinstance(block, collections.Iterable):
                for item in block:
                    item_report_str = ReportString(item)
                    if not (item_report_str.matches(ReportItemPattern.DATE)
                            or
                            item_report_str.matches(ReportItemPattern.TIME)):
                        new_data.append(item)
                        first = True
                    elif first:
                        new_data.append(ReportItemKey.BREAK.as_string())
                        first = False
            self.blocks.replace(datetime_key, ReportBlock(new_data))
        return datetime_column, time_num, date_result
