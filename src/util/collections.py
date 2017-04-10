import collections
from typing import List, Iterable, Tuple, Callable, TypeVar, Generic, Iterator, Any, Union

T = TypeVar('T')
U = TypeVar('U')
R = TypeVar('R')


def is_list_or_tuple(instance) -> bool:
    if isinstance(instance, (list, tuple)):
        return True
    return False


def _func_extend(inner_func: Union[map, filter]) -> Callable[[Iterable[T],
                                                              Callable[[T], Any],
                                                              Tuple[Callable[[T], Any], ...]],
                                                             Iterator[Any]]:
    def func(iterable: Iterable[T], first_action: Callable[[T], Any],
             *other_actions: Callable[[T], Any]) -> Iterator[Any]:
        if other_actions:
            return func(inner_func(first_action, iterable), *other_actions)
        return inner_func(first_action, iterable)
    return func

map_extend = _func_extend(map)
filter_extend = _func_extend(filter)


def are_equal(a: Iterable[T], b: Iterable[T]) -> bool:
    new_a = list(a)
    new_b = list(b)
    return len(new_a) == len([i for i, j in zip(new_a, new_b) if i == j])


# TODO: Try to make it collections.Iterable
class Block(Generic[T], collections.Iterable):

    def __init__(self, inner_list: List[T]):
        self.__inner_list = inner_list

    def __len__(self):
        return len(self.__inner_list)

    def __getitem__(self, indices: slice):
        return self.__inner_list[indices]

    def __iter__(self):
        return iter(self.__inner_list)

    @property
    def inner_list(self) -> List[T]:
        return self.__inner_list

    def extend(self, block: 'Block[T]'):
        self.inner_list.extend(block.inner_list)

    def eliminate_voids(self):
        self.__inner_list = list(filter(len, self.inner_list))

    def divide_into_parts(self, parts_lengths: Iterable[int]) -> List[List[T]]:
        parts = []
        block = self.inner_list[:]
        for length in parts_lengths:
            parts.append(block[0: length])
            block = block[length:]
        return parts

    def is_equal_to(self, other: 'Block[T]') -> bool:
        return are_equal(self.inner_list, other.inner_list)

    @staticmethod
    def _get_item_excluder(items: Iterable[T]) -> Callable[[T], bool]:
        def not_belongs_to_items(item: T) -> bool:
            return item not in items
        return not_belongs_to_items

    def filter_excluding_items(self, items: Iterable[T]) -> Iterator[T]:
        item_excluder = self._get_item_excluder(items)
        return filter(item_excluder, self.inner_list)

    def replace_by_index(self, index: int, replacement: T):
        self.inner_list[index] = replacement

    def remove_by_index(self, index: Union[None, int]):
        if index is not None:
            del self.inner_list[index]

    def remove_by_indices(self, start_index: int, finish_index: int):
        del self.inner_list[start_index:finish_index]
