def calc_percent(value, percentage):
    result = value * (percentage / 100)
    return result

def remap(value, srcMin, srcMax, resMin, resMax):
    srcRange = srcMax - srcMin
    if srcRange == 0:
        return resMin
    else:
        resRange = resMax - resMin
        return (((value - srcMin) * resRange) / srcRange) + resMin
