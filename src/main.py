from pathlib import Path
from typing import Iterable

from src.patient import Patient
from src.report_logging import LOGGER
from src.chart import PatientChart
from src.file_process import ReportFileProcessor
from src.report_logging import ReportEventMessageBuilder, ReportsStatistics
from src.report_dataframe import PatientDataFrame
from src.util import paths
from src.report import Report
from src.util.paths import Extension


INPUT_DIR = Path('..', "raw")
INPUT_EXT = Extension.PDF
OUTPUT_DIR = Path('..', "output")
OUTPUT_EXT = Extension.CSV
OUTPUT_FILE_NAME = "output"
OUTPUT_PATH = Path(OUTPUT_DIR, OUTPUT_FILE_NAME)


def stream_patients_with_logging(reports_paths: Iterable[Path],
                                 report_statistics: ReportsStatistics):
    reports_paths = list(reports_paths)
    for index, path in enumerate(reports_paths):
        start_num = index + 1
        report = __build_report_with_logging(start_num, path, report_statistics)
        yield Patient(report)


def __build_report(report_path: Path) -> Report:
    report_file = ReportFileProcessor(report_path)
    blocks = report_file.blocks
    report_name = report_path.stem
    return Report(report_name, blocks)


def __build_report_with_logging(index: int, path: Path, statistics: ReportsStatistics) -> Report:
    report_name = path.stem
    message_builder = ReportEventMessageBuilder(report_name, index, statistics)
    try:
        report = __build_report(path)
        if report.success:
            message = message_builder.create_message("has been parsed")
            LOGGER.info(message)
        else:
            message = message_builder.create_message("has been parsed with missing values (%s)"
                                                     % report.message)
            LOGGER.warning(message)
        return report
    except (KeyError, TypeError, ValueError) as err:
        message = message_builder.create_message("has not been parsed")
        statistics.inc_counter_of_fails()
        LOGGER.error(message)
        LOGGER.debug(err)


def main():
    reports_paths = list(paths.collect_dir_content_by_extension(INPUT_DIR, Extension.PDF))
    statistics = ReportsStatistics(reports_paths)
    patients = []
    for patient in stream_patients_with_logging(reports_paths, statistics):
        patients.append(patient)
    patient_chart = PatientChart(patients)
    patient_chart.save_figures(OUTPUT_DIR, OUTPUT_FILE_NAME)
    LOGGER.info("Sizes of groups: %s" % patient_chart.sizes_of_groups)
    patient_dataframe = PatientDataFrame(patients)
    patient_dataframe.save_csv(OUTPUT_DIR, OUTPUT_FILE_NAME, separator=',')
    LOGGER.info("Successfully handled: %d/%d"
                % (statistics.number_of_successes, statistics.number_of_reports))
    LOGGER.info("Press ENTER to exit")
    input()


if __name__ == '__main__':
    paths.create_dir(OUTPUT_DIR)
    main()
