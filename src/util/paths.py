from enum import Enum
from os import makedirs
from pathlib import Path
from typing import Iterable, Callable, List, Iterator, Union

_FILE_SEARCH_BY_EXTENSION_PATTERN = "*.%s"


class Extension(Enum):
    """
    Extension type
    """
    JSON = "json"
    CSV = "csv"
    PYTHON = "py"
    EXECUTABLE = "exe"
    PDF = "pdf"
    PNG = "png"

    def as_string(self):
        return self.value


def _ext_to_str(ext: Union[Extension, str]):
    """
    Cast 'ExtensionType' or 'str' instance to 'str' type
    :param ext: 'ExtensionType' or 'str' instance
    :return: 'str' instance
    """
    if isinstance(ext, Extension):
        value = ext.as_string()
    else:
        value = ext
    return value


def extend_file_name(file_name: str, ext: Extension) -> str:
    """
    Add extension to the file name
    :param file_name: a name of the file
    :param ext: an extension of the file
    :return: a full name of the file
    """
    ext = _ext_to_str(ext)
    return '.'.join((file_name, ext))


def create_dir(dir_path: Path):
    if not dir_path.exists():
        makedirs(str(dir_path))


def collect_dir_content_by_extension(dir_path: Union[str, Path], ext: Extension) -> Iterable[Path]:
    file_search_pattern = _get_file_search_pattern_by_extension(ext.value)
    path_generator = collect_dir_content_by_pattern(dir_path, file_search_pattern)
    return path_generator


def _get_file_search_pattern_by_extension(ext: str) -> str:
    return _FILE_SEARCH_BY_EXTENSION_PATTERN % ext


def collect_dir_content_by_pattern(dir_path: Union[str, Path],
                                   pattern: str) -> Iterable[Path]:
    dir_path = Path(dir_path)
    path_generator = dir_path.glob(pattern)
    return path_generator


class PathList(object):

    def __init__(self, inner_list: List[Path]):
        self.__inner_list = inner_list

    @property
    def inner_list(self) -> List[Path]:
        return self.__inner_list

    @staticmethod
    def _get_name_excluder(names: Iterable[str]) -> Callable[[Path], bool]:
        def not_belongs_to_file_names(path: Path) -> bool:
            return path.name not in names
        return not_belongs_to_file_names

    def filter_excluding_names(self, names: Iterable[str]) -> Iterator[Path]:
        name_excluder = self._get_name_excluder(names)
        return filter(name_excluder, self.inner_list)
