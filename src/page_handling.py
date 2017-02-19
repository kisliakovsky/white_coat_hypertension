from collections import defaultdict

from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextLine, LTTextBox
from pdfminer.pdfdocument import PDFDocument, PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from src.util import list_util as lutil
from src.util import string_util as sutil
from src.util.string_util import StringJoiner

_EXTRA_FONT_INFO = "(cid:9)"

BREAK_SJ = StringJoiner('\n')
DEF_SJ = StringJoiner()


def _compare_coords(item_bbox, block_bbox):
    lb_coords_flag = item_bbox[0] >= block_bbox[0] and item_bbox[1] >= block_bbox[1]
    rt_coords_flag = item_bbox[2] <= block_bbox[2] and item_bbox[3] <= block_bbox[3]
    return lb_coords_flag and rt_coords_flag

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

_BLOCK_KEYS = (_ALL_KEY, _PATIENT_KEY, _DAY_NIGHT_KEY, _READINGS_BP_KEY,
               _AVG_BP_KEY, _WHITE_COAT_WINDOW_KEY, _NIGHTTIME_DIP_KEY, _VALUES_KEY,
               _VALUES_1_SD_KEY, _VALUES_1_HR_KEY, _VALUES_2_SD_KEY, _VALUES_2_HR_KEY,
               _VALUES_3_SD_KEY, _VALUES_3_HR_KEY, _VALUES_4_SD_KEY, _VALUES_4_HR_KEY)

_PATIENT_BBOX = (50, 635, 210, 720)
_DAY_NIGHT_BBOX = (50, 500, 210, 635)
_READINGS_BP_BBOX = (50, 380, 210, 490)
_AVG_BP_BBOX = (210, 380, 435, 490)
_WHITE_COAT_WINDOW_BBOX = (435, 412, 560, 490)
_NIGHT_TIME_DIP_BBOX = (435, 380, 560, 418)
_VALUES_BBOX = (50, 80, 560, 380)
_VALUES_1_SD_BBOX = (50, 80, 140, 380)
_VALUES_1_HR_BBOX = (140, 80, 177, 380)
_VALUES_2_SD_BBOX = (177, 80, 267, 380)
_VALUES_2_HR_BBOX = (267, 80, 304, 380)
_VALUES_3_SD_BBOX = (304, 80, 410, 380)
_VALUES_3_HR_BBOX = (410, 80, 432, 380)
_VALUES_4_SD_BBOX = (432, 80, 530, 380)
_VALUES_4_HR_BBOX = (530, 80, 560, 380)

_PATIENT_KB = (_PATIENT_KEY, _PATIENT_BBOX)
_DAY_NIGHT_KB = (_DAY_NIGHT_KEY, _DAY_NIGHT_BBOX)
_READINGS_BP_KB = (_READINGS_BP_KEY, _READINGS_BP_BBOX)
_AVG_BP_KB = (_AVG_BP_KEY, _AVG_BP_BBOX)
_WHITE_COAT_WINDOW_KB = (_WHITE_COAT_WINDOW_KEY, _WHITE_COAT_WINDOW_BBOX)
_NIGHTTIME_DIP_KB = (_NIGHTTIME_DIP_KEY, _NIGHT_TIME_DIP_BBOX)
_VALUES_KB = (_VALUES_KEY, _VALUES_BBOX)
_VALUES_1_KB = (_VALUES_1_SD_KEY, _VALUES_1_SD_BBOX, _VALUES_1_HR_KEY, _VALUES_1_HR_BBOX)
_VALUES_2_KB = (_VALUES_2_SD_KEY, _VALUES_2_SD_BBOX, _VALUES_2_HR_KEY, _VALUES_2_HR_BBOX)
_VALUES_3_KB = (_VALUES_3_SD_KEY, _VALUES_3_SD_BBOX, _VALUES_3_HR_KEY, _VALUES_3_HR_BBOX)
_VALUES_4_KB = (_VALUES_4_SD_KEY, _VALUES_4_SD_BBOX, _VALUES_4_HR_KEY, _VALUES_4_HR_BBOX)


def _update_page_text_dict(blocks, l_obj):
    # bbox means a bounding box, which is a four-part tuple of the object's page position: (x0, y0, x1, y1)
    # The x0 value tells the left offset for a given piece of text,
    # and the x1 value tells how wide it is.
    item_bbox = tuple(l_obj.bbox)
    # print(l_obj)
    if _compare_coords(item_bbox, _VALUES_KB[1]):
        blocks[_VALUES_KB[0]].append(l_obj.get_text())
        if _compare_coords(item_bbox, _VALUES_1_KB[1]):
            blocks[_VALUES_1_KB[0]].append(l_obj.get_text())
        elif _compare_coords(item_bbox, _VALUES_1_KB[3]):
            blocks[_VALUES_1_KB[2]].append(l_obj.get_text())
        elif _compare_coords(item_bbox, _VALUES_2_KB[1]):
            blocks[_VALUES_2_KB[0]].append(l_obj.get_text())
        elif _compare_coords(item_bbox, _VALUES_2_KB[3]):
            blocks[_VALUES_2_KB[2]].append(l_obj.get_text())
        elif _compare_coords(item_bbox, _VALUES_3_KB[1]):
            blocks[_VALUES_3_KB[0]].append(l_obj.get_text())
        elif _compare_coords(item_bbox, _VALUES_3_KB[3]):
            blocks[_VALUES_3_KB[2]].append(l_obj.get_text())
        elif _compare_coords(item_bbox, _VALUES_4_KB[1]):
            blocks[_VALUES_4_KB[0]].append(l_obj.get_text())
        elif _compare_coords(item_bbox, _VALUES_4_KB[3]):
            blocks[_VALUES_4_KB[2]].append(l_obj.get_text())
    elif _compare_coords(item_bbox, _PATIENT_KB[1]):
        blocks[_PATIENT_KB[0]].append(l_obj.get_text())
    elif _compare_coords(item_bbox, _DAY_NIGHT_KB[1]):
        blocks[_DAY_NIGHT_KB[0]].append(l_obj.get_text())
    elif _compare_coords(item_bbox, _READINGS_BP_KB[1]):
        blocks[_READINGS_BP_KB[0]].append(l_obj.get_text())
    elif _compare_coords(item_bbox, _AVG_BP_KB[1]):
        blocks[_AVG_BP_KB[0]].append(l_obj.get_text())
    elif _compare_coords(item_bbox, _WHITE_COAT_WINDOW_KB[1]):
        blocks[_WHITE_COAT_WINDOW_KB[0]].append(l_obj.get_text())
    elif _compare_coords(item_bbox, _NIGHTTIME_DIP_KB[1]):
        blocks[_NIGHTTIME_DIP_KB[0]].append(l_obj.get_text())


# noinspection PyDefaultArgument
def _parse_layout(layout):
    # The key for each entry is a tuple of the bbox's (x0, x1) points,
    # and the corresponding value is a list of text strings found within that bbox.
    # So by grouping text which starts at the same horizontal plane and has the same width,
    # all paragraphs belonging to the same column can be aggregated,
    # regardless of their vertical position or length.
    # Conceptually, each entry in the page_text dictionary represents all the text
    # associated with each physical column.
    blocks = defaultdict(list)
    for l_item in layout:
        if isinstance(l_item, LTTextBox) or isinstance(l_item, LTTextLine):
            _update_page_text_dict(blocks, l_item)
            blocks[_ALL_KEY].append(l_item.get_text())
    for key in _BLOCK_KEYS:
        blocks[key] = ''.join(blocks[key]).split('\n')
        blocks[key] = lutil.map_with_ops([lambda s: s.lstrip().rstrip(),  # move to page_handling
                                          lambda s: s.replace(_EXTRA_FONT_INFO, ''),
                                          lambda s: ' '.join(s.split())], blocks[key])
        blocks[key] = lutil.filter_with_ops([len, lambda s: not sutil.is_empty_entry(s)], blocks[key])
    return blocks


def _parse_pages(doc):
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    text_content = []
    for page in PDFPage.create_pages(doc):
        interpreter.process_page(page)
        layout = device.get_result()
        text_content.append(_parse_layout(layout))
        break  # first page
    return text_content


def with_pdf(file_name, op):
    res = None
    with open(file_name, "rb") as raw_file:
        parser = PDFParser(raw_file)
        doc = PDFDocument(parser)
        if doc.is_extractable:
            res = op(doc)
        else:
            raise PDFTextExtractionNotAllowed
    return res


def get_pages(file_name):
    return with_pdf(file_name, _parse_pages)
