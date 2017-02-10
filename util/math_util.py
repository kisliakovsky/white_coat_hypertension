def parse_quantity(s):
    res = s.split(' ')
    if len(res) == 2:
        return {
            "value": res[0],
            "unit": res[1]
        }


def split_list_by_values(a_list):
    min_list = []
    max_list = []
    min_val = min(a_list)
    max_val = max(a_list)
    for n in a_list:
        if abs(n - min_val) < abs(n - max_val):
            min_list.append(n)
        else:
            max_list.append(n)
    return min_list, max_list


def mean(numbers):
    return float(sum(numbers)) / max(len(numbers), 1)


