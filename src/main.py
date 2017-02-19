import os
from os import listdir, makedirs, path
from pathlib import Path
from sys import stderr

import src.page_handling as ph

from src.report import Report, ReportDataFrame


def _collect_report_paths(input_dir, input_ext):
    report_paths = []
    for report_file in listdir(input_dir):
        report_path = path.join(input_dir, report_file)
        if path.isfile(report_path) and (report_file.endswith(input_ext) or report_file.endswith(input_ext.upper())):
            report_paths.append(report_path)
    return report_paths


def _extract_report_data(report_path):
    report_raw_data = ph.get_pages(report_path)[0]
    return report_raw_data

INPUT_DIR = os.path.join('..', "raw")
INPUT_EXT = ".pdf"
OUTPUT_DIR = os.path.join('..', "output")
OUTPUT_EXT = ".csv"
OUTPUT_FILE = "output"
if not path.exists(OUTPUT_DIR):
    makedirs(OUTPUT_DIR)
OUTPUT_BASE_NAME = path.join(OUTPUT_DIR, OUTPUT_FILE)


def main():
    r_paths = _collect_report_paths(INPUT_DIR, INPUT_EXT)
    reports = []
    r_paths_num = len(r_paths)
    success_num = 0
    fails_num = 0
    for i, r_path in enumerate(r_paths):
        r_raw_data = _extract_report_data(r_path)
        report = None
        report_name = path.basename(path.normpath(r_path))
        report_num = i + 1
        try:
            report = Report(r_raw_data)
            if not report.success:
                print("%s (Report %s)" % (report.message, report_name), file=stderr)
        except (TypeError, ValueError):
            print("Report %s has NOT been parsed (%d/%d)" % (report_name, report_num, r_paths_num), file=stderr)
            fails_num += 1
        if report:
            reports.append(report)
            print("Report %s has been parsed (%d/%d)" % (report_name, report_num, r_paths_num))
            success_num += 1
    report_df = ReportDataFrame(reports)
    cntr = 1
    while True:
        output = "%s_%d%s" % (OUTPUT_BASE_NAME, cntr, OUTPUT_EXT)
        cntr += 1
        output_path = Path(output)
        if output_path.is_file():
            continue
        else:
            report_df.save_csv(output, separator=';')
            break
    print("The number of processed reports (success/fail/total): %d/%d/%d" %
          (success_num, fails_num, r_paths_num))
    print("The output file was saved as %s" % Path(output).absolute())
    input('Press ENTER to exit')

if __name__ == '__main__':
    main()

