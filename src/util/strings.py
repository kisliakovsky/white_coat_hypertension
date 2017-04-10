from typing import Union

# delimiter for key-value pair
ENTRY_DELIMITER = ':'
# delimiter for quantity-unit pair
VALUE_DELIMITER = ' '


def remove_extra_spaces(string: str) -> str:
    return string.lstrip().rstrip()


def is_empty(string: str) -> bool:
    return len(string) == 0


def is_not_empty(string: str) -> bool:
    return not is_empty(string)


def is_entry(s):
    return ENTRY_DELIMITER in s


def is_empty_entry(s):
    if is_entry(s):
        value = get_value_of_entry(s)
        return len(value) == 0
    else:
        return False


def is_not_empty_entry(string: str) -> bool:
    return not is_empty_entry(string)


def get_value_of_entry(s):
    if is_entry(s):
        entry = s.split(ENTRY_DELIMITER)
        value = entry[1].lstrip().rstrip()
        return value


def to_str(bytes_or_str: Union[bytes, str]) -> str:
    """
    Cast 'str' or 'bytes' instance to 'str' type
    :param bytes_or_str: 'str' or 'bytes' instance
    :return: 'str' instance
    """
    if isinstance(bytes_or_str, bytes):
        value = bytes_or_str.decode('utf-8')
    else:
        value = bytes_or_str
    return value


def to_bytes(bytes_or_str: Union[bytes, str]) -> bytes:
    """
    Cast 'str' or 'bytes' instance to 'bytes' type
    :param bytes_or_str: 'str' or 'bytes' instance
    :return: 'bytes' instance
    """
    if isinstance(bytes_or_str, str):
        value = bytes_or_str.encode('utf-8')
    else:
        value = bytes_or_str
    return value
