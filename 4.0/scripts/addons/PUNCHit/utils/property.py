
def rotate_list(list, amount):
    for i in range(abs(amount)):
        if amount > 0:
            list.append(list.pop(0))
        else:
            list.insert(0, list.pop(-1))

    return list


def shorten_float_string(float_str, count=4):
    
    split = float_str.split('.')

    if len(split) == 2:
        return f"{split[0]}.{split[1][:count].rstrip('0').rstrip('.')}"
    else:
        return float_str
