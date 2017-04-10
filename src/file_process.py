from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Tuple, Union, Iterable, NewType, Dict, Callable, List

from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextLine, LTTextBox, LTPage
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from src.report_item import ReportBlock
from src.util import collections
from src.util import strings

_EXTRA_FONT_INFO = "(cid:9)"


def remove_extra_font_info(string: str) -> str:
    return string.replace(_EXTRA_FONT_INFO, '')

ReportBlockCoordinates = NewType('ReportBlockCoordinates', Tuple[float, float, float, float])


class ReportSpace(Enum):

    ALL = (0, 0, 560, 760),
    PATIENT = (50, 635, 210, 720),
    DAY_NIGHT = (50, 500, 210, 635),
    READINGS_BP = (50, 380, 210, 490),
    AVG_BP = (210, 380, 435, 490),
    WHITE_COAT_WINDOW = (435, 412, 560, 490),
    NIGHT_TIME_DIP = (435, 380, 560, 418),

    VALUES = (50, 80, 560, 380),

    VALUES_1_COLUMN_SD = (50, 80, 140, 380),
    VALUES_1_COLUMN_HR = (140, 80, 177, 380),
    VALUES_2_COLUMN_SD = (177, 80, 267, 380),
    VALUES_2_COLUMN_HR = (267, 80, 304, 380),
    VALUES_3_COLUMN_SD = (304, 80, 410, 380),
    VALUES_3_COLUMN_HR = (410, 80, 432, 380),
    VALUES_4_COLUMN_SD = (432, 80, 530, 380),
    VALUES_4_COLUMN_HR = (530, 80, 560, 380),

    def __new__(cls, coordinates: ReportBlockCoordinates):
        index = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = index, coordinates
        obj.__index = index
        return obj

    def __init__(self, coordinates):
        self.__coordinates = coordinates

    # TODO: Turn it back.
    @property
    def index(self) -> int:
        return self.__index

    @classmethod
    def indices(cls):
        for item in cls:
            yield item.index

    @property
    def coordinates(self) -> Tuple[int, int, int, int]:
        return self.__coordinates

    def includes_item(self, item: Union[LTTextBox, LTTextLine]) -> bool:
        block_coords = self.__coordinates
        item_coords = tuple(item.bbox)
        return ReportSpace._corresponds_to_borders(block_coords, item_coords)

    @staticmethod
    def _corresponds_to_borders(block_coords: ReportBlockCoordinates,
                                item_coords: ReportBlockCoordinates) -> bool:
        left_bottom_border_x_match = item_coords[0] >= block_coords[0]
        left_bottom_border_y_match = item_coords[1] >= block_coords[1]
        left_bottom_border_match = left_bottom_border_x_match and left_bottom_border_y_match
        right_top_border_x_match = item_coords[2] <= block_coords[2]
        right_top_border_y_match = item_coords[3] <= block_coords[3]
        right_top_border_match = right_top_border_x_match and right_top_border_y_match
        return left_bottom_border_match and right_top_border_match


class InvalidPdfError(Exception):
    pass


class BlockStore(object):

    def __init__(self, blocks: Dict[int, ReportBlock]):
        self.__inner_store = blocks

    def get(self, key: ReportSpace) -> Union[None, ReportBlock]:
        try:
            return self.__inner_store[key.index]
        except KeyError:
            return None

    def replace(self, key: ReportSpace, block: ReportBlock):
        self.__inner_store[key.index] = block


class ReportFileProcessor(object):

    _COMPLEX_VALUES_BLOCK_SPACES = [ReportSpace.PATIENT, ReportSpace.DAY_NIGHT,
                                    ReportSpace.READINGS_BP, ReportSpace.AVG_BP,
                                    ReportSpace.WHITE_COAT_WINDOW,
                                    ReportSpace.NIGHT_TIME_DIP]
    _VALUE_COLUMN_SPACES = [ReportSpace.VALUES_1_COLUMN_SD,
                            ReportSpace.VALUES_1_COLUMN_HR,
                            ReportSpace.VALUES_2_COLUMN_SD,
                            ReportSpace.VALUES_2_COLUMN_HR,
                            ReportSpace.VALUES_3_COLUMN_SD,
                            ReportSpace.VALUES_3_COLUMN_HR,
                            ReportSpace.VALUES_4_COLUMN_SD,
                            ReportSpace.VALUES_4_COLUMN_HR]

    def __init__(self, path: Path):
        blocks = ReportFileProcessor.__parse_document(path, ReportFileProcessor.extract_blocks)
        self.__blocks = blocks

    @staticmethod
    def extract_blocks(document: PDFDocument) -> BlockStore:
        page = ReportFileProcessor.__extract_page(document)
        page_layout = ReportFileProcessor.__extract_page_layout(page)
        blocks = ReportFileProcessor.__extract_blocks(page_layout)
        return blocks

    @property
    def blocks(self) -> BlockStore:
        return self.__blocks

    @staticmethod
    def __parse_document(path: Path,
                         blocks_extractor: Callable[[PDFDocument], BlockStore]) -> BlockStore:
        with open(str(path), "rb") as raw_file:
            parser = PDFParser(raw_file)
            document = PDFDocument(parser)
            if document.is_extractable:
                return blocks_extractor(document)
            else:
                raise InvalidPdfError

    @staticmethod
    def __extract_page(document: PDFDocument) -> PDFPage:
        page_generator = PDFPage.create_pages(document)
        for page in page_generator:
            return page

    @staticmethod
    def __extract_page_layout(page: PDFPage) -> LTPage:
        resource_manager = PDFResourceManager()
        layout_analysis_parameters = LAParams()
        device = PDFPageAggregator(resource_manager, laparams=layout_analysis_parameters)
        page_interpreter = PDFPageInterpreter(resource_manager, device)
        page_interpreter.process_page(page)
        page_layout = device.get_result()
        return page_layout

    @staticmethod
    def __process_item_text(text: str) -> List[str]:
        text_chunks = ''.join(text).split('\n')
        # TODO: Why do the split-join function needed?
        text_chunks = list(collections.map_extend(text_chunks,
                                                  strings.remove_extra_spaces,
                                                  remove_extra_font_info,
                                                  lambda s: ' '.join(s.split())))
        text_chunks = list(collections.filter_extend(text_chunks, strings.is_not_empty,
                                                     strings.is_not_empty_entry))
        return text_chunks

    @staticmethod
    def __extract_blocks(layout: LTPage) -> BlockStore:
        blocks = defaultdict(list)
        for item in layout:
            if isinstance(item, LTTextBox) or isinstance(item, LTTextLine):
                block_keys = ReportFileProcessor.define_block_keys(item)
                text_chunks = ReportFileProcessor.__process_item_text(item.get_text())
                for block_key in block_keys:
                    current_block = blocks[block_key]
                    if current_block:
                        current_block.extend(ReportBlock(text_chunks))
                    else:
                        blocks[block_key] = ReportBlock(text_chunks[:])

        block_store = BlockStore(dict(blocks))
        return block_store

    @staticmethod
    def define_block_keys(item: Union[LTTextBox, LTTextLine]) -> Iterable[int]:
        keys = [ReportSpace.ALL.index]
        if ReportSpace.VALUES.includes_item(item):
            keys.append(ReportSpace.VALUES.index)
            for value_column_space in ReportFileProcessor._VALUE_COLUMN_SPACES:
                if value_column_space.includes_item(item):
                    keys.append(value_column_space.index)
                    break
            return keys
        for block_space in ReportFileProcessor._COMPLEX_VALUES_BLOCK_SPACES:
            if block_space.includes_item(item):
                keys.append(block_space.index)
                break
        return keys
