sensor_types = {'Custom':[0,0],
                'Super 8':[5.79,4.01],
                'Super 16':[12.52,7.41],
                '1 inch':[13.2,8.8],
                'Micro 4/3':[17.3,13],
                'APS-C':[23.6,15.6],
                'APS-H':[27.9,18.6],
                'Super 35':[24.89,18.66],
                'Fullframe':[36,24],
                'Alexa 65':[54.12,25.58],
                '6x6 MF':[56,56],
                'IMAX 70mm':[70,48.5],
                '6x9 MF':[84,56],
                }

def sensor_type_items(self,context):
    enum = []
    for st in sensor_types:
        enum.append((st, st, ''))
    return enum
