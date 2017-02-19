import operator
from sys import stderr
from collections import defaultdict
# noinspection PyPep8Naming
from datetime import datetime as DateTime
# noinspection PyPep8Naming
from datetime import timedelta as TimeDelta

import numpy as np
from pandas import DataFrame

import util.string_util as sutil
import util.list_util as lutil
import util.math_util as mutil


class Report(object):

    _TITLE_PATTERN = r"[Rr]eport"
    _PHYSICIAN_PATTERN = r"[Pp]hysician"
    _DATE_PATTERN = r"\d+.\d+.\d{4}"
    _TIME_PATTERN = r"\d+:\d{2}$"
    _WHITESPACE_PATTERN = r"^\s*$"
    _PERIOD_PATTERN = r"[Pp]eriod"
    _STUDY_DATE_PATTERN = r"[Ss]tudy [Dd]ate"
    _AWAKE_ASLEEP_PATTERN = r"wake.*sleep"
    _BLOOD_PRESSURE_THRESHOLD_PATTERN = r"[Bb][Pp] [Tt]hreshold"
    _BLOOD_PRESSURE_LOAD_PATTERN = r"[Bb][Pp] [Ll]oad"
    _PAGINATOR_PATTERN = r"[Pp]age.*of.*"
    _READINGS_PATTERN = r"^[Rr]eadings$"
    _TOTAL_READINGS_PATTERN = r"[Tt]otal [Rr]eadings"
    _SUCCESSFUL_READINGS_PATTERN = r"\d+\s*\(\d+.*%\)"
    _PATIENT_ID_LEN_BOUND = (3, 10)
    _PATIENT_ID_PATTERN = r"^\d{%d,%d}$" % _PATIENT_ID_LEN_BOUND
    _PATIENT_NAME_PATTERN = r"[\w\.]+ \w+"
    _PATIENT_SEX_PATTERN = r"^([Ff]em|[Mm])ale$"
    _DATE_TIME_SYS_PATTERN = r"[Dd]ate.*/.*[Tt]ime.*[Ss]ys"
    _HEART_RATE_PATTERN = r"^HR$"
    _SYSTOLIC_PATTERN = r"^Sys$"
    _DIASTOLIC_PATTERN = r"^Dia$"
    _AVG_BLOOD_PRESSURE_PATTERN = r"[Aa]verage [Bb]lood [Pp]ressure"
    _24_HOURS_PATTERN = r"24-h.*"
    _AWAKE_PATTERN = r"^Awake$"
    _ASLEEP_PATTERN = r"^Asleep$"
    _MAP_PP_PATTERN = r"[Mm][Aa][Pp] [Pp][Pp]"
    _TWO_THREE_DIGITS_NUM_PATTERN = r"^\d{2,3}$"
    _PARENTHESES_NUM_PATTERN = r"^\(\d+\)$"
    _COMMA_NUM_PATTERN = r"^\d+,\d+$"
    _WHITE_COAT_WINDOW_PATTERN = r"[Ww]hite [Cc]oat [Ww]indow"
    _FIRST_HOUR_PATTERN = r"1st.*h.*[Mm]ax"
    _NIGHTTIME_DIP_PATTERN = r"[Nn]ight.*[Dd]ip.*%"
    _DIP_PATTERN = r"^[Dd]ip%$"
    _PERIOD_TIME_PATTERN = r"^[Tt]ime$"
    _PERIOD_INTERVAL_PATTERN = r"^[Ii]nterval$"
    _BREAK_PATTERN = r"^break$"

    _TIME_KEY = "time"
    _INTERVAL_KEY = "interval"
    _PERIOD_KPS = tuple(zip((_TIME_KEY, _INTERVAL_KEY),
                            (_PERIOD_TIME_PATTERN, _PERIOD_INTERVAL_PATTERN)))
    _DAY_KEY = "day"
    _NIGHT_KEY = "night"
    _DAY_NIGHT_KEYS = (_DAY_KEY, _NIGHT_KEY)
    _TOTAL_READINGS_KEY = "total"
    _SUCCESSFUL_READINGS_KEY = "success"
    _READINGS_PAIR = (_READINGS_PATTERN, tuple(zip((_TOTAL_READINGS_KEY, _SUCCESSFUL_READINGS_KEY),
                                                   (_TOTAL_READINGS_PATTERN, _SUCCESSFUL_READINGS_PATTERN))))
    DATETIME_KEY = "dt"
    SYSTOLIC_KEY = "sys"
    DIASTOLIC_KEY = "dia"
    HEART_RATE_KEY = "hr"
    _MEAN_ARTERIAL_PRESSURE_KEY = "map"
    _PULSE_PRESSURE_KEY = "pp"
    _VALUES_KEYS = SYSTOLIC_KEY, DIASTOLIC_KEY, HEART_RATE_KEY
    # _AVG_COL_KEYS = _VALUES_KEYS + (_MEAN_ARTERIAL_PRESSURE_KEY, _PULSE_PRESSURE_KEY)
    _AVG_COL_KEYS = _VALUES_KEYS
    _VALUES_PATTERNS = _SYSTOLIC_PATTERN, _DIASTOLIC_PATTERN, _HEART_RATE_PATTERN
    _VALUES_KPS = tuple(zip(_VALUES_KEYS, _VALUES_PATTERNS))
    TWENTY_FOUR_HOURS_KEY = "24h"
    AWAKE_KEY = "awake"
    ASLEEP_KEY = "asleep"
    _AVG_ROW_KEYS = TWENTY_FOUR_HOURS_KEY, AWAKE_KEY, ASLEEP_KEY

    READINGS_KEY = "readings"
    FIRST_HOUR_KEY = "first_hour"
    _WHITE_COAT_WINDOW_KEYS = READINGS_KEY, FIRST_HOUR_KEY
    DIP_KEY = "dip"

    _DATE_FORMAT = "%d.%m.%Y"
    _TIME_FORMAT = "%H:%M"
    _DATE_TIME_FORMAT = "%s %s" % (_DATE_FORMAT, _TIME_FORMAT)

    _ALL_KEY = "all"
    _PATIENT_KEY = "patient"
    _DAY_NIGHT_KEY = "daynight"
    _READINGS_BP_KEY = "readbp"
    _AVG_BP_KEY = "avg"
    _WHITE_COAT_WINDOW_KEY = "wcw"
    _NIGHTTIME_DIP_KEY = "ntd"
    _VALUES_KEY = "values"
    _VALUES_1_SD_KEY = "values1sd"
    _VALUES_1_HR_KEY = "values1hr"
    _VALUES_2_SD_KEY = "values2sd"
    _VALUES_2_HR_KEY = "values2hr"
    _VALUES_3_SD_KEY = "values3sd"
    _VALUES_3_HR_KEY = "values3hr"
    _VALUES_4_SD_KEY = "values4sd"
    _VALUES_4_HR_KEY = "values4hr"
    _VALUES_SD_KEYS = (_VALUES_1_SD_KEY, _VALUES_2_SD_KEY, _VALUES_3_SD_KEY, _VALUES_4_SD_KEY)
    _VALUES_HR_KEYS = (_VALUES_1_HR_KEY, _VALUES_2_HR_KEY, _VALUES_3_HR_KEY, _VALUES_4_HR_KEY)
    _WHITE_COAT_WINDOW_KP = (_WHITE_COAT_WINDOW_KEY, _WHITE_COAT_WINDOW_PATTERN)
    _NIGHTTIME_DIP_KP = (_NIGHTTIME_DIP_KEY, _NIGHTTIME_DIP_PATTERN)

    _MAX_COLUMN_VALUES_NUM = 25

    _BREAK_KEY = "break"

    def __init__(self, blocks):
        self.__blocks = blocks
        self.__raw_data = blocks[Report._ALL_KEY]
        self.__remove_item(Report._PAGINATOR_PATTERN)
        self.__title = self.__remove_item(Report._TITLE_PATTERN)
        self.__physician = self.__handle_and_remove_item(Report._PHYSICIAN_PATTERN, sutil.get_value_of_entry)
        self.__period = self.__parse_period()
        self.__study_date = self.__handle_and_remove_item(Report._STUDY_DATE_PATTERN,
                                                          lambda item: sutil.search_in_str(Report._DATE_PATTERN, item))
        self.__awake, self.__asleep = self.__parse_awake_asleep()
        self.__bp_threshold = self.__parse_bp_threshold()
        self.__readings = self.__parse_readings()
        self.__bp_load = self.__parse_bp_load()
        self.__remove_item(Report._PERIOD_PATTERN)
        patient_id = self.__remove_item(Report._PATIENT_ID_PATTERN, Report._PATIENT_KEY)
        if not patient_id:
            patient_id = self.__remove_item(Report._PATIENT_ID_PATTERN)
        self.__patient_id = "'%s'" % patient_id
        patient_name = self.__remove_item(Report._PATIENT_NAME_PATTERN, Report._PATIENT_KEY)
        if not patient_name:
            patient_name = self.__remove_item(Report._PATIENT_NAME_PATTERN)
        self.__patient_name = patient_name
        self.__patient_sex, self.__patient_age, self.__patient_date_of_birth = self.__parse_sex_age_dob_triplet()
        self.__avg_bp = self.__parse_avg_bp()
        self.__white_coat_window = self.__parse_white_coat_window()
        self.__nighttime_dip = self.__parse_nighttime_dip()
        self.__values, success, message = self.__parse_values()
        self.__success = success
        self.__message = message

    @property
    def blocks(self):
        return self.__blocks

    @property
    def raw_data(self):
        return self.__raw_data

    @property
    def title(self):
        return self.__title

    @property
    def physician(self):
        return self.__physician

    @property
    def period(self):
        return self.__period

    @property
    def study_date(self):
        return self.__study_date

    @property
    def awake(self):
        return self.__awake

    @property
    def asleep(self):
        return self.__asleep

    @property
    def bp_threshold(self):
        return self.__bp_threshold

    @property
    def readings(self):
        return self.__readings

    @property
    def bp_load(self):
        return self.__bp_load

    @property
    def patient_id(self):
        return self.__patient_id

    @property
    def patient_name(self):
        return self.__patient_name

    @property
    def patient_sex(self):
        return self.__patient_sex

    @property
    def patient_age(self):
        return self.__patient_age

    @property
    def patient_date_of_birth(self):
        return self.__patient_date_of_birth

    @property
    def values(self):
        return self.__values

    @property
    def avg_bp(self):
        return self.__avg_bp

    @property
    def nighttime_dip(self):
        return self.__nighttime_dip

    @property
    def white_coat_window(self):
        return self.__white_coat_window

    @property
    def success(self):
        return self.__success

    @property
    def message(self):
        return self.__message

    def __search_first_in_list(self,  pattern, block_key=_ALL_KEY, remove_after=False, replace_after=None):
        return lutil.search_first_in_list(self.__blocks[block_key], pattern, remove_after, replace_after)

    def __search_sequence_in_list(self, header_pattern, num, block_key=_ALL_KEY, remove_after=False):
        return lutil.search_sequence_in_list(self.__blocks[block_key], header_pattern, num, remove_after)

    def __search_among_neighbors(self, i, neighbor_pattern, block_key=_ALL_KEY, remove_after=False):
        return lutil.search_among_neighbors(self.__blocks[block_key], i, neighbor_pattern, remove_after)

    def __remove_item(self,  pattern, block_key=_ALL_KEY):
        return self.__search_first_in_list(pattern, block_key, remove_after=True)

    def __replace_item(self, pattern, replace_after, block_key=_ALL_KEY):
        return self.__search_first_in_list(pattern, block_key, replace_after=replace_after)

    def __handle_and_remove_item(self, pattern, handle_op, block_key=_ALL_KEY):
        res = self.__remove_item(pattern, block_key)
        if res:
            res = handle_op(res)
        return res

    def __parse_period(self):
        period = {}
        self.__remove_item(Report._PERIOD_PATTERN, Report._DAY_NIGHT_KEY)
        num_of_values = 2
        _, period_times = self.__search_sequence_in_list(Report._PERIOD_KPS[0][1], num_of_values,
                                                         Report._DAY_NIGHT_KEY, remove_after=True)
        _, period_intervals = self.__search_sequence_in_list(Report._PERIOD_KPS[1][1], num_of_values,
                                                             Report._DAY_NIGHT_KEY, remove_after=True)
        if period_times and period_intervals:
            for i, key in enumerate(Report._DAY_NIGHT_KEYS):
                period[key] = {Report._PERIOD_KPS[0][0]: period_times[i],
                               Report._PERIOD_KPS[1][0]: mutil.parse_quantity(period_intervals[i])}
        return period

    def __parse_awake_asleep(self):
        awake = None
        asleep = None
        num_of_values = 2
        _, awake_asleep = self.__search_sequence_in_list(Report._AWAKE_ASLEEP_PATTERN, num_of_values,
                                                         Report._DAY_NIGHT_KEY, remove_after=True)
        if awake_asleep:
            awake = sutil.get_value_of_entry(awake_asleep[0])
            asleep = sutil.get_value_of_entry(awake_asleep[1])
        return awake, asleep

    def __parse_readings(self):
        readings = {}
        self.__remove_item(Report._READINGS_PAIR[0])
        for pair in Report._READINGS_PAIR[1]:
            readings[pair[0]] = self.__handle_and_remove_item(pair[1], sutil.get_value_of_entry,
                                                              Report._READINGS_BP_KEY)
        return readings

    def __parse_bp_value(self, pattern, block, op):
        bp_val = {}
        num_of_values = 2
        _, periods = self.__search_sequence_in_list(pattern, num_of_values, block, remove_after=True)
        if periods:
            for i, key in enumerate(Report._DAY_NIGHT_KEYS):
                bp_val[key] = op(key, periods[i])
        return bp_val

    def __parse_bp_threshold(self):
        return self.__parse_bp_value(Report._BLOOD_PRESSURE_THRESHOLD_PATTERN,
                                     Report._DAY_NIGHT_KEY,
                                     lambda key, period: mutil.parse_quantity(sutil.get_value_of_entry(period)))

    def __parse_bp_load(self):
        return self.__parse_bp_value(Report._BLOOD_PRESSURE_LOAD_PATTERN,
                                     Report._READINGS_BP_KEY,
                                     lambda key, period:
                                     sutil.cut_if_start_with(key, period, trim=True, case_sense=False))

    def __parse_sex_age_dob_triplet(self):
        num_of_values = 2
        patient_sex, age_and_birth_date = self.__search_sequence_in_list(Report._PATIENT_SEX_PATTERN, num_of_values,
                                                                         Report._PATIENT_KEY)
        patient_age = None
        patient_date_of_birth = None
        if age_and_birth_date:
            patient_age = age_and_birth_date[0]
            try:
                patient_date_of_birth = age_and_birth_date[1]
                num_of_values = 2
                self.__search_sequence_in_list(Report._PATIENT_SEX_PATTERN, num_of_values,
                                               Report._PATIENT_KEY, remove_after=True)
            except ValueError:
                pass
        return patient_sex, patient_age, patient_date_of_birth

    _REMOVE_SHIFT = 2

    def __parse_avg_bp_24h_row(self):
        row = []
        key_idx_pairs = []
        for key_pattern in Report._VALUES_KPS:
            idx, _ = self.__search_first_in_list(key_pattern[1], Report._AVG_BP_KEY)
            key_idx_pairs.append((key_pattern[0], idx))
        key_idx_pairs.sort(key=operator.itemgetter(1))
        val_dict = {}
        for i, key_idx_pair in enumerate(key_idx_pairs):
            _, avg_br_fr_val = self.__search_among_neighbors(key_idx_pair[1] - Report._REMOVE_SHIFT * i,
                                                             Report._TWO_THREE_DIGITS_NUM_PATTERN,
                                                             Report._AVG_BP_KEY, remove_after=True)
            val_dict[key_idx_pair[0]] = avg_br_fr_val
        for key in Report._VALUES_KEYS:
            row.append(int(val_dict[key]))
        self.__remove_item(Report._24_HOURS_PATTERN, Report._AVG_BP_KEY)
        return row

    def __parse_avg_bp(self):
        avg_bp = defaultdict(dict)
        self.__remove_item(Report._AVG_BLOOD_PRESSURE_PATTERN, Report._AVG_BP_KEY)
        for i in range(9):
            self.__remove_item(Report._PARENTHESES_NUM_PATTERN, Report._AVG_BP_KEY)
        twenty_four_h_vals = self.__parse_avg_bp_24h_row()
        num_of_values = 3

        def parse_avg_seq_vals(pattern):
            _, vals = self.__search_sequence_in_list(pattern, num_of_values, Report._AVG_BP_KEY, remove_after=True)
            for k in range(len(vals)):
                try:
                    vals[k] = int(vals[k])
                except ValueError:
                    pass
            return vals
        awake_vals = parse_avg_seq_vals(Report._AWAKE_PATTERN)
        asleep_vals = parse_avg_seq_vals(Report._ASLEEP_PATTERN)
        all_vals = (twenty_four_h_vals, awake_vals, asleep_vals)
        for i, row in enumerate(all_vals):
            for j, val in enumerate(row):
                avg_bp[Report._AVG_COL_KEYS[j]][Report._AVG_ROW_KEYS[i]] = val
        return avg_bp

    def __parse_white_coat_window(self):
        white_coat_window = defaultdict(dict)
        self.__remove_item(Report._WHITE_COAT_WINDOW_KP[1], Report._WHITE_COAT_WINDOW_KP[0])
        self.__remove_item(Report._NIGHTTIME_DIP_PATTERN, Report._WHITE_COAT_WINDOW_KP[0])
        self.__remove_item(Report._READINGS_PATTERN, Report._WHITE_COAT_WINDOW_KP[0])
        self.__remove_item(Report._FIRST_HOUR_PATTERN, Report._WHITE_COAT_WINDOW_KP[0])
        num_of_values = 2

        def parse_wcw_seq_vals(pattern):
            _, vals = self.__search_sequence_in_list(pattern, num_of_values,
                                                     Report._WHITE_COAT_WINDOW_KP[0], remove_after=True)
            for k in range(len(vals)):
                try:
                    vals[k] = int(vals[k])
                except ValueError:
                    pass
            return vals
        sys_vals = parse_wcw_seq_vals(Report._VALUES_KPS[0][1])
        dia_vals = parse_wcw_seq_vals(Report._VALUES_KPS[1][1])
        hr_vals = parse_wcw_seq_vals(Report._VALUES_KPS[2][1])
        all_vals = [sys_vals, dia_vals, hr_vals]
        for i, row in enumerate(all_vals):
            for j, val in enumerate(row):
                white_coat_window[Report._VALUES_KPS[i][0]][Report._WHITE_COAT_WINDOW_KEYS[j]] = val
        return white_coat_window

    def __parse_nighttime_dip(self):
        nighttime_dip = defaultdict(dict)
        self.__remove_item(Report._NIGHTTIME_DIP_PATTERN[1], Report._NIGHTTIME_DIP_KP[0])

        def parse_ntd_seq_val(pattern):
            _, vals = self.__search_sequence_in_list(pattern, 1,
                                                     Report._NIGHTTIME_DIP_KP[0], remove_after=True)
            corr_delim_val = vals[0].replace(',', '.')
            try:
                corr_delim_val = float(corr_delim_val)
            except ValueError:
                pass
            return corr_delim_val
        for i in range(2):
            nighttime_dip[Report._VALUES_KPS[i][0]][Report.DIP_KEY] = parse_ntd_seq_val(Report._VALUES_KPS[i][1])
        return nighttime_dip

    def __parse_values(self):
        all_vals = {}
        dt_cols, t_nums = self.__parse_dt_cols(remove_after=True)
        hr_cols = self.__parse_hr_cols(t_nums)
        sd_cols, (success, message) = self.__parse_sd_cols(t_nums)
        sys_cols, dia_cols = sd_cols
        for _ in t_nums:
            all_vals[Report.DATETIME_KEY] = [item for sublist in dt_cols for item in sublist]
            all_vals[Report.SYSTOLIC_KEY] = [item for sublist in sys_cols for item in sublist]
            all_vals[Report.DIASTOLIC_KEY] = [item for sublist in dia_cols for item in sublist]
            all_vals[Report.HEART_RATE_KEY] = [item for sublist in hr_cols for item in sublist]
        return all_vals, success, message

    def __parse_sd_cols(self, t_nums):
        sys_cols = []
        dia_cols = []
        message = None
        global_success = True
        for i, t_num in enumerate(t_nums):
            res, local_success = self.__parse_sd_col(Report._VALUES_SD_KEYS[i], t_num)
            if not local_success:
                global_success = local_success
                message = "Please enter the values of periodic measurements of " \
                          "the blood pressure (systolic and diastolic) of the column #%d manually" % (i + 1)
            sys_col, dia_col = res
            if sys_col:
                sys_cols.append(sys_col)
            if dia_col:
                dia_cols.append(dia_col)
        return (sys_cols, dia_cols), (global_success, message)

    def __parse_sd_col(self, sd_key, t_num):
        sys_col = []
        dia_col = []
        sd_col = []
        num_group = []
        block = self.blocks[sd_key]
        if not block:
            return sys_col, dia_col
        idx, _ = self.__search_first_in_list(Report._TWO_THREE_DIGITS_NUM_PATTERN, sd_key)
        while idx < len(block):
            val = block[idx]
            match = sutil.search_in_str(Report._TWO_THREE_DIGITS_NUM_PATTERN, val)
            if match:
                num_group.append(int(val))
            elif num_group:
                sd_col.append(num_group)
                num_group = []
            idx += 1
        if num_group:
            sd_col.append(num_group)
        col_pair = None

        def distribute_columns_by_mean(columns):
            if mutil.mean(columns[0]) < mutil.mean(columns[1]):
                columns[0], columns[1] = columns[1], columns[0]

        def merge_columns(col_first_part, col_second_part):
            cols = [col_first_part[0] + col_second_part[0], col_first_part[1] + col_second_part[1]]
            return cols

        def distribute_and_merge_columns(col_first_part, col_second_part):
            distribute_columns_by_mean(col_first_part)
            distribute_columns_by_mean(col_second_part)
            return merge_columns(col_first_part, col_second_part)

        def process_columns(columns):
            columns = columns[:2]
            return [each[0] for each in columns], [each[1] for each in columns]

        def process_double_columns(columns):
            k, columns = columns[0]
            half_len = int(len(columns) / 2)
            return k, [columns[:half_len], columns[half_len:]]

        def clear_values(indices):
            for index in sorted(indices, reverse=True):
                del sd_col[index]

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
                        idx, double_sd_sp = process_double_columns(double_sd_sp)
                        remove_indices.append(idx)
                        col_pair = distribute_and_merge_columns(sd_fp, double_sd_sp)
                        clear_values(remove_indices)
                    elif sd_full_len >= 1:
                        indcs, sd_full = process_columns(sd_full)
                        col_pair = [sd_fp[0] + sd_fp[1], sd_full[0]]
                        distribute_columns_by_mean(col_pair)
                        clear_values(indcs)
                elif double_sd_fp_len >= 1:
                    idx, double_sd_fp = process_double_columns(double_sd_fp)
                    remove_indices.append(idx)
                    if sd_sp_len >= 2:
                        indcs, sd_sp = process_columns(sd_sp)
                        remove_indices.extend(indcs)
                        col_pair = distribute_and_merge_columns(double_sd_fp, sd_sp)
                        clear_values(remove_indices)
                    elif double_sd_sp_len >= 1:
                        idx, double_sd_sp = process_double_columns(double_sd_sp)
                        remove_indices.append(idx)
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
                col_pair = [['' for i in range(tn_full)] for j in range(2)]
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

    def __parse_hr_cols(self, t_nums):
        hr_cols = []
        for i, t_num in enumerate(t_nums):
            hr_col = self.__parse_hr_col(Report._VALUES_HR_KEYS[i], t_num)
            if hr_col:
                hr_cols.append(hr_col)
        return hr_cols

    def __parse_hr_col(self, hr_key, t_num):
        hr_col = []
        num_group = []
        block = self.blocks[hr_key]
        if not block:
            return hr_col
        idx, _ = self.__search_first_in_list(Report._TWO_THREE_DIGITS_NUM_PATTERN, hr_key)
        while idx < len(block):
            val = block[idx]
            match = sutil.search_in_str(Report._TWO_THREE_DIGITS_NUM_PATTERN, val)
            if match:
                num_group.append(int(val))
            elif num_group:
                hr_col.append(num_group)
                num_group = []
            idx += 1
        if num_group:
            hr_col.append(num_group)
        if isinstance(t_num, tuple):
            buff = []
            for num in t_num:
                for part in hr_col:
                    if num == len(part):
                        buff.append(part)
                        break
            if len(buff) == len(t_num):
                hr_col = [item for sublist in buff for item in sublist]
            elif len(hr_col[0]) == sum(t_num):
                hr_col = hr_col[0]
            else:
                print("Wrong number of values", file=stderr)
        else:
            if len(hr_col[0]) == t_num:
                hr_col = hr_col[0]
            else:
                print("Wrong number of values", file=stderr)
        return hr_col

    def __parse_dt_cols(self, remove_after=False):
        dt_cols = []
        t_nums = []
        date_res = None
        for key in Report._VALUES_SD_KEYS:
            dt_col, t_num, date_res = self.__parse_dt_col(key, remove_after, date_res)
            if dt_col:
                dt_cols.append(dt_col)
                t_nums.append(t_num)
        return dt_cols, t_nums

    def __parse_dt_col(self, dt_key, remove_after=False, date_res=None):
        dt_col = []
        cntr = 0
        times = []
        time_num = []
        block = self.blocks[dt_key]
        if not block:
            return dt_col, 0, date_res
        if not date_res:
            _, date_res = self.__search_first_in_list(Report._DATE_PATTERN, dt_key)
        idx, time_res = self.__search_first_in_list(Report._TIME_PATTERN, dt_key)
        while idx < len(block):
            val = block[idx]
            match = sutil.search_in_str(Report._DATE_PATTERN, val)
            if match:
                dt_col.extend(times)
                time_num.append(cntr)
                date_res = val
                times = []
                cntr = 0
            else:
                match = sutil.search_in_str(Report._TIME_PATTERN, val)
                if match:
                    time_res = val
                    dt = " ".join((date_res, time_res))
                    times.append(DateTime.strptime(dt, Report._DATE_TIME_FORMAT))
                    cntr += 1
                elif times:
                    dt_col.extend(times)
                    if len(time_num) > 0 and time_num[0] == 0:
                        time_num[0] = cntr
                    else:
                        time_num.append(cntr)
                    times = []
                    cntr = 0
            idx += 1
        if times:
            dt_col.extend(times)
            time_num.append(cntr)
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
            for item in block:
                if not (sutil.search_in_str(Report._DATE_PATTERN, item)
                        or
                        sutil.search_in_str(Report._TIME_PATTERN, item)):
                    new_data.append(item)
                    first = True
                elif first:
                    new_data.append(Report._BREAK_KEY)
                    first = False
            self.__blocks[dt_key] = new_data
        return dt_col, time_num, date_res


class ReportDataFrame(object):

    _ID_KEY = "Id"
    _PATIENT_NAME_KEY = "Name"
    _DATE_OF_BIRTH_KEY = "DOB"
    _BP_PHENOTYPE_KEY = "BP phenotype"
    _BP_PROFILE_KEY = "BP profile"
    _LAST_HOUR_MAX_SYS_BP_KEY = "Last hour max sBP"
    _SINGLE_KEYS = (_ID_KEY, _PATIENT_NAME_KEY, _DATE_OF_BIRTH_KEY, _BP_PHENOTYPE_KEY,
                    _BP_PROFILE_KEY, _LAST_HOUR_MAX_SYS_BP_KEY)
    _AVG_DAY_KEY = "Avg BP per day"
    _AVG_AWAKE_KEY = "Avg BP while awake"
    _AVG_ASLEEP_KEY = "Avg BP while asleep"
    _AVG_KEYS = (_AVG_DAY_KEY, _AVG_AWAKE_KEY, _AVG_ASLEEP_KEY)
    _FIRST_HOUR_MAX_KEY = "BP max 1st hour"
    _MSD_ALL_SYS_KEY = "sMSD all"
    _MSD_DAY_SYS_KEY = "sMSD day (07-23)"
    _MSD_ALT_DAY_SYS_KEY = "sMSD day (10-20)"
    _MSD_NIGHT_SYS_KEY = "sMSD night (23-07)"
    _MSD_ALT_NIGHT_SYS_KEY = "sMSD night (00-06)"
    _MSD_ALL_DIA_KEY = "dMSD all"
    _MSD_DAY_DIA_KEY = "dMSD day (07-23)"
    _MSD_ALT_DAY_DIA_KEY = "dMSD day (10-20)"
    _MSD_NIGHT_DIA_KEY = "dMSD night (23-07)"
    _MSD_ALT_NIGHT_DIA_KEY = "dMSD night (00-06)"
    _MSD_KEYS = (_MSD_ALL_SYS_KEY, _MSD_DAY_SYS_KEY, _MSD_ALT_DAY_SYS_KEY,
                 _MSD_NIGHT_SYS_KEY, _MSD_ALT_NIGHT_SYS_KEY, _MSD_ALL_DIA_KEY,
                 _MSD_DAY_DIA_KEY, _MSD_ALT_DAY_DIA_KEY, _MSD_NIGHT_DIA_KEY,
                 _MSD_ALT_NIGHT_DIA_KEY)
    _DAY_TIME_KEY = "Awake time"
    _NIGHT_TIME_KEY = "Asleep time"
    _EXTRA_TIME_KEY = "Extra time"
    _SYSTOLIC_KEY = "sBP"
    _DIASTOLIC_KEY = "dBP"
    _HEART_RATE_KEY = "HR"
    _MEASUREMENT_KEYS = (_SYSTOLIC_KEY, _DIASTOLIC_KEY, _HEART_RATE_KEY)

    _DATE_FORMAT = "%d.%m.%Y"
    _TIME_FORMAT = "%H:%M"
    _DATETIME_FORMAT = "%s %s" % (_DATE_FORMAT, _TIME_FORMAT)

    _TIME_INTERVAL = TimeDelta(minutes=15)
    _START_TIME = DateTime.strptime("01.01.1970 8:00", _DATETIME_FORMAT)
    _FINISH_TIME = DateTime.strptime("02.01.1970 17:00", _DATETIME_FORMAT) + _TIME_INTERVAL
    _TIME_PERIOD = _FINISH_TIME - _START_TIME
    _FIRST_DAY_START_TIME = DateTime.strptime("01.01.1970 7:00", _DATETIME_FORMAT)
    _FIRST_NIGHT_START_TIME = DateTime.strptime("01.01.1970 23:00", _DATETIME_FORMAT)
    _ALT_FIRST_DAY_START_TIME = DateTime.strptime("01.01.1970 10:00", _DATETIME_FORMAT)
    _ALT_FIRST_DAY_FINISH_TIME = DateTime.strptime("01.01.1970 20:00", _DATETIME_FORMAT)
    _ALT_FIRST_NIGHT_START_TIME = DateTime.strptime("02.01.1970 00:00", _DATETIME_FORMAT)
    _ALT_FIRST_NIGHT_END_TIME = DateTime.strptime("02.01.1970 06:00", _DATETIME_FORMAT)
    _DAY_LEN = _FIRST_NIGHT_START_TIME - _FIRST_DAY_START_TIME
    _NIGHT_LEN = _FIRST_DAY_START_TIME + _TIME_PERIOD - _FIRST_NIGHT_START_TIME
    _TIME_INTERVAL_NUM = int(_TIME_PERIOD / _TIME_INTERVAL)

    def __new__(cls, *args, **kwargs):
        cls.DAY_NIGHT_INTERVALS = cls._calc_day_night_intervals()
        cls.DAY_NIGHT_ALT_INTERVALS = cls._calc_day_night_alt_intervals()
        return super(ReportDataFrame, cls).__new__(cls)

    def __init__(self, reports):
        ReportDataFrame._calc_day_night_intervals()
        self.__columns = ReportDataFrame._prepare_columns()
        data = []
        for report in reports:
            data.append(ReportDataFrame._prepare_data(report))
        self.__frame = DataFrame(np.asarray(data), columns=self.__columns)

    @staticmethod
    def _prepare_data(report):
        measure_keys = (Report.SYSTOLIC_KEY, Report.DIASTOLIC_KEY, Report.HEART_RATE_KEY)
        # noinspection PyListCreation
        data = []
        data.append(report.patient_id)
        data.append(report.patient_name)
        data.append(report.patient_date_of_birth)
        data.append(_calc_blood_pressure_phenotype(report.avg_bp, report.white_coat_window))
        data.append(_calc_blood_pressure_profile(report.nighttime_dip))
        report_values = report.values
        dts = report_values[Report.DATETIME_KEY]
        last_idx = len(dts) - 1
        last_hour = dts[-1] - TimeDelta(hours=1)
        last_hour_idx = last_idx
        for i, dt in enumerate(dts):
            if dt >= last_hour:
                last_hour_idx = i
        syss = report_values[Report.SYSTOLIC_KEY][last_hour_idx: last_idx + 1]
        last_hour_max_sys = '-'
        try:
            if isinstance(syss, list):
                last_hour_max_sys = max(syss)
            else:
                last_hour_max_sys = syss
        except ValueError:
            pass
        data.append(last_hour_max_sys)
        for outer in (Report.TWENTY_FOUR_HOURS_KEY, Report.AWAKE_KEY, Report.ASLEEP_KEY):
            for inner in measure_keys:
                val = report.avg_bp[inner][outer]
                try:
                    val = float(val)
                except ValueError:
                    pass
                data.append(val)
        data.append(report.white_coat_window[Report.SYSTOLIC_KEY][Report.FIRST_HOUR_KEY])
        time_columns = []
        curr_time = ReportDataFrame._START_TIME
        for i in range(ReportDataFrame._TIME_INTERVAL_NUM):
            time_columns.append(curr_time.time())
            curr_time += ReportDataFrame._TIME_INTERVAL
        index = 0
        measure_dates = report_values[Report.DATETIME_KEY]
        measure_dates_num = len(measure_dates)
        sys_all = []
        dia_all = []
        for time in time_columns:
            if index < measure_dates_num:
                report_time = measure_dates[index].time()
            else:
                report_time = None
            if report_time == time:
                sys_all.append(report_values[Report.SYSTOLIC_KEY][index])
                dia_all.append(report_values[Report.DIASTOLIC_KEY][index])
                for key in measure_keys:
                    data.append(report_values[key][index])
                index += 1
            else:
                sys_all.append(None)
                dia_all.append(None)
                for _ in measure_keys:
                    data.append("")
        dn_intervals = [v for k, v in ReportDataFrame.DAY_NIGHT_INTERVALS]
        dna_intervals = [v for k, v in ReportDataFrame.DAY_NIGHT_ALT_INTERVALS]
        sys_intervals = lutil.split_list(sys_all, dn_intervals)
        dia_intervals = lutil.split_list(dia_all, dn_intervals)
        sysa_intervals = lutil.split_list(sys_all, dna_intervals)
        diaa_intervals = lutil.split_list(dia_all, dna_intervals)
        sys_all = lutil.filter_list_by_value(sys_all, None)
        dia_all = lutil.filter_list_by_value(dia_all, None)
        sys_intervals = [lutil.filter_list_by_value(lst, None) for lst in sys_intervals]
        dia_intervals = [lutil.filter_list_by_value(lst, None) for lst in dia_intervals]
        sysa_intervals = [lutil.filter_list_by_value(lst, None) for lst in sysa_intervals][1::2]
        diaa_intervals = [lutil.filter_list_by_value(lst, None) for lst in diaa_intervals][1::2]
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
        first_day_length = ReportDataFrame._FIRST_NIGHT_START_TIME - ReportDataFrame._START_TIME
        intervals.append((ReportDataFrame._DAY_TIME_KEY, int(first_day_length / ReportDataFrame._TIME_INTERVAL)))
        sec_day_start_time = ReportDataFrame._FIRST_DAY_START_TIME + twenty_four_hours
        first_night_length = sec_day_start_time - ReportDataFrame._FIRST_NIGHT_START_TIME
        intervals.append((ReportDataFrame._NIGHT_TIME_KEY, int(first_night_length / ReportDataFrame._TIME_INTERVAL)))
        sec_day_length = ReportDataFrame._FINISH_TIME - sec_day_start_time
        intervals.append((ReportDataFrame._DAY_TIME_KEY, int(sec_day_length / ReportDataFrame._TIME_INTERVAL)))
        return intervals

    @staticmethod
    def _calc_day_night_alt_intervals():
        twenty_four_hours = TimeDelta(hours=24)
        intervals = []
        extra_length = ReportDataFrame._ALT_FIRST_DAY_START_TIME - ReportDataFrame._START_TIME
        intervals.append((ReportDataFrame._EXTRA_TIME_KEY, int(extra_length / ReportDataFrame._TIME_INTERVAL)))
        first_day_length = ReportDataFrame._ALT_FIRST_DAY_FINISH_TIME - ReportDataFrame._ALT_FIRST_DAY_START_TIME
        intervals.append((ReportDataFrame._DAY_TIME_KEY, int(first_day_length / ReportDataFrame._TIME_INTERVAL)))
        extra_length = ReportDataFrame._ALT_FIRST_NIGHT_START_TIME - ReportDataFrame._ALT_FIRST_DAY_FINISH_TIME
        intervals.append((ReportDataFrame._EXTRA_TIME_KEY, int(extra_length / ReportDataFrame._TIME_INTERVAL)))
        first_night_length = ReportDataFrame._ALT_FIRST_NIGHT_END_TIME - ReportDataFrame._ALT_FIRST_NIGHT_START_TIME
        intervals.append((ReportDataFrame._NIGHT_TIME_KEY, int(first_night_length / ReportDataFrame._TIME_INTERVAL)))
        sec_day_start_time = ReportDataFrame._ALT_FIRST_DAY_START_TIME + twenty_four_hours
        extra_length = sec_day_start_time - ReportDataFrame._ALT_FIRST_NIGHT_END_TIME
        intervals.append((ReportDataFrame._EXTRA_TIME_KEY, int(extra_length / ReportDataFrame._TIME_INTERVAL)))
        sec_day_length = ReportDataFrame._FINISH_TIME - sec_day_start_time
        intervals.append((ReportDataFrame._DAY_TIME_KEY, int(sec_day_length / ReportDataFrame._TIME_INTERVAL)))
        return intervals

    @staticmethod
    def _prepare_columns():

        header_rows = []

        header_row = []
        for key in ReportDataFrame._SINGLE_KEYS:
            header_row.append(key)
        for key in ReportDataFrame._AVG_KEYS:
            for _ in ReportDataFrame._MEASUREMENT_KEYS:
                header_row.append(key)
        header_row.append(ReportDataFrame._FIRST_HOUR_MAX_KEY)
        # noinspection PyUnresolvedReferences
        for day_night_key, num in ReportDataFrame.DAY_NIGHT_INTERVALS:
            for i in range(num):
                for _ in ReportDataFrame._MEASUREMENT_KEYS:
                    header_row.append(day_night_key)
        for msd_key in ReportDataFrame._MSD_KEYS:
            header_row.append(msd_key)
        header_rows.append(header_row)

        header_row = []
        for _ in ReportDataFrame._SINGLE_KEYS:
            header_row.append("")
        for _ in ReportDataFrame._AVG_KEYS:
            for key in ReportDataFrame._MEASUREMENT_KEYS:
                header_row.append(key)
        header_row.append("")
        time_columns = []
        curr_time = ReportDataFrame._START_TIME
        for i in range(ReportDataFrame._TIME_INTERVAL_NUM):
            time_columns.append('%s' % curr_time.time().strftime(ReportDataFrame._TIME_FORMAT))
            curr_time += ReportDataFrame._TIME_INTERVAL
        for time_column in time_columns:
            for _ in ReportDataFrame._MEASUREMENT_KEYS:
                header_row.append(time_column)
        for _ in ReportDataFrame._MSD_KEYS:
            header_row.append("")
        header_rows.append(header_row)

        header_row = []
        middle_keys_len = len(ReportDataFrame._SINGLE_KEYS)
        middle_keys_len += len(ReportDataFrame._AVG_KEYS) * len(ReportDataFrame._MEASUREMENT_KEYS) + 1
        for i in range(middle_keys_len):
            header_row.append("")
        for _ in time_columns:
            for key in ReportDataFrame._MEASUREMENT_KEYS:
                header_row.append(key)
        for _ in ReportDataFrame._MSD_KEYS:
            header_row.append("")
        header_rows.append(header_row)

        return header_rows

    @property
    def frame(self):
        return self.__frame

    def save_csv(self, file_name, encoding=None, separator=','):
        self.__frame.to_csv(file_name, encoding=encoding, index=False, sep=separator)

EMPTY_VALUE_STR = "--"


def _calc_blood_pressure_profile(night_time_dip):
    ntd_sys = night_time_dip[Report.SYSTOLIC_KEY][Report.DIP_KEY]
    if ntd_sys == EMPTY_VALUE_STR:
        return EMPTY_VALUE_STR
    if 10 < ntd_sys <= 20:
        return 1
    elif 0 < ntd_sys <= 10:
        return 2
    elif ntd_sys <= 0:
        return 3
    elif 20 < ntd_sys:
        return 4


_BP_AWAKE_SYS_NORM = 135
_DIFF_BP_SYS_NORM = 10


# noinspection PyChainedComparisons
def _calc_blood_pressure_phenotype(avg_bp, white_coat_window):
    avg_bp_sys = avg_bp[Report.SYSTOLIC_KEY][Report.AWAKE_KEY]
    wcw_sys = white_coat_window[Report.SYSTOLIC_KEY][Report.FIRST_HOUR_KEY]
    if wcw_sys == EMPTY_VALUE_STR:
        return EMPTY_VALUE_STR
    diff = abs(avg_bp_sys - wcw_sys)
    if avg_bp_sys < _BP_AWAKE_SYS_NORM and wcw_sys < _BP_AWAKE_SYS_NORM and diff < _DIFF_BP_SYS_NORM:
        return 1
    elif avg_bp_sys < _BP_AWAKE_SYS_NORM and wcw_sys < _BP_AWAKE_SYS_NORM and diff >= _DIFF_BP_SYS_NORM:
        return 2
    elif (avg_bp_sys >= _BP_AWAKE_SYS_NORM or wcw_sys >= _BP_AWAKE_SYS_NORM) and diff < _DIFF_BP_SYS_NORM:
        return 3
    elif avg_bp_sys >= _BP_AWAKE_SYS_NORM and wcw_sys < _BP_AWAKE_SYS_NORM and diff >= _DIFF_BP_SYS_NORM:
        return 4
    elif avg_bp_sys < _BP_AWAKE_SYS_NORM and wcw_sys >= _BP_AWAKE_SYS_NORM and diff >= _DIFF_BP_SYS_NORM:
        return 5
    elif avg_bp_sys >= _BP_AWAKE_SYS_NORM and wcw_sys >= _BP_AWAKE_SYS_NORM and diff >= _DIFF_BP_SYS_NORM:
        return 6
