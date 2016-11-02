from decimal import *
from copy import deepcopy

def replace_floats(obj):
    if isinstance(obj, list):
        for i in obj:
            obj[i] = replace_floats(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = replace_floats(obj[k])
        return obj
    elif isinstance(obj, float):
        if obj % 1 == 0:
            return int(obj)
        else:
            return Decimal(obj)
    else:
        return obj 

class Order:
    def __init__(self):
        self.__f = 1.2

    def f2d(self):
        c = deepcopy(self)
        for a in c.__dict__:
            v = getattr(c, a)
            setattr(c, a, replace_floats(v))
        return c

    def myprint(self):
        print(self.__f)


o = Order()
o.myprint()
o2d = o.f2d()
o2d.myprint()
