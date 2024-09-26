
from functools import cache
import math
from typing import Self


class Unit:

    base_units = ['m', 'kg', 's'] #add others

    def __init__(self, **base_units):
        non_base_units = [unit for unit in base_units if unit not in Unit.base_units]
        if non_base_units:
            raise ValueError(f"Ivalid base unit(s): {non_base_units}.")
        self.base_units = base_units

    def __hash__(self):
        return hash(tuple(self.base_units.items()))
        
    def __eq__(self, other):
        return all(self[base_unit] == other[base_unit] for base_unit in Unit.base_units)

    def __getitem__(self, base_unit):
        return self.base_units[base_unit]

    def quantity(self, value):
        if not any(self.base_units.values()):
            return value
        for QuantityType in Quantity.__subclasses__():
            if QuantityType is not UndefinedQuantity and QuantityType.unit == self:
                return QuantityType(value)
        return UndefinedQuantity(value, unit=self)
    
    def __str__(self):
        return '*'.join(symbol if power == 1 else f"{symbol}^{power}" for symbol, power in self.base_units.items() if power)

    @cache
    @staticmethod
    def make(**base_units):
        defaults = {base_unit: 0 for base_unit in Unit.base_units}
        return Unit(**dict(defaults, **base_units))
    
    @cache
    @staticmethod
    def _make(**base_units):
        return Unit(**base_units)
    
    def __invert__(self):
        base_units = {base_unit: - self[base_unit] for base_unit in Unit.base_units}
        return Unit.make(**base_units)
    
    def __mul__(self, other):
        base_units = {base_unit: self[base_unit] + other[base_unit] for base_unit in Unit.base_units}
        return Unit.make(**base_units)
    
    def __truediv__(self, other):
        return self*~other


class Quantity:
    def __init__(self, value):
        self.value = value

    def __hash__(self):
        return hash((self.value, self.unit))

    def __repr__(self) -> str:
        return f"{self.value}{self.unit}"
    
    def __str__(self) -> str:
        #TODO: move rounding to __fmt__
        return f"{round(self.value*self.fmt_scale)}{self.fmt_unit}"
    
    def __neg__(self) -> Self:
        return self.unit.quantity(-self.value)
    
    def __add__(self, other: Self) -> Self:
        if other is 0:
            return self
        if self.unit != other.unit:
            raise TypeError("Can only add quantities of same type together")
        return self.unit.quantity(self.value + other.value)
    
    def __radd__(self, other: Self) -> Self:
        return self + other
    
    def __sub__(self, other: Self) -> Self:
        return self + -other
    
    def __mul__(self, other: int | float | Self) -> Self:
        if isinstance(other, (int, float)):
            unit = self.unit
            value = self.value*other
        else:
            unit = self.unit*other.unit
            value = self.value*other.value
        return unit.quantity(value)
    
    def __rmul__(self, other: int | float) -> Self:
        return self*other
    
    def __truediv__(self, other: int | float | Self) -> Self:
        if isinstance(other, (int, float)):
            unit = self.unit
            value = self.value/other
        else:
            unit = self.unit/other.unit
            value = self.value/other.value
        # if not any(unit.base_units.values()):
        #     return value
        return unit.quantity(value)
    
    def __rtruediv__(self, other: int | float) -> Self:
        if not isinstance(other, (int, float)):
            raise TypeError()
        value = other/self.value
        unit = ~self.unit
        return unit.quantity(value)
    
    def __ceil__(self) -> Self:
        return self.unit.quantity(math.ceil(self.value))
    
    def __floor__(self) -> Self:
        return self.unit.quantity(math.floor(self.value))
    
    def __eq__(self, other: Self) -> bool:
        if self.unit != other.unit:
            raise TypeError()
        return math.isclose(self.value, other.value)
    
    def __lt__(self, other: Self) -> bool:
        if self.unit != other.unit:
            raise TypeError()
        return self.value < other.value and self != other
    
    def __le__(self, other: Self) -> bool:
        if self.unit != other.unit:
            raise TypeError()
        return self.value <= other.value or self == other
    
    def __gt__(self, other: Self) -> bool:
        if self.unit != other.unit:
            raise TypeError()
        return self.value > other.value and self != other
    
    def __ge__(self, other: Self) -> bool:
        if self.unit != other.unit:
            raise TypeError()
        return self.value >= other.value or self == other
    

class UndefinedQuantity(Quantity):

    fmt_scale = 1

    def __init__(self, value, unit):
        Quantity.__init__(self, value)
        self.unit = unit

    @property
    def fmt_unit(self) -> str:
        return str(self.unit)


class Time(Quantity):

    unit = Unit.make(s=1)

    fmt_unit = 's'

    fmt_scale = 1

    sec_per_min = 60

    min_per_hour = 60

    def __init__(self, sec=0, min=0, hour=0):
        self.value = sec + Time.sec_per_min*(min + Time.min_per_hour*hour)

    @staticmethod
    def create(sec, min=0, hour=0) -> Self:
        return Time(sec + Time.sec_per_min*(min + Time.min_per_hour*hour))

    @property
    def sec(self) -> int:
        return int(self.value%Time.sec_per_min)
    
    @property
    def min(self) -> int:
        return int((self.value//Time.sec_per_min)%Time.min_per_hour)
    
    @property
    def hour(self) -> int:
        return int(self.value//(Time.sec_per_min*Time.min_per_hour))

    def __str__(self) -> str:
        if self.value < 0:
            return f"-{-self}"
        else:
            return f"{self.hour}:{self.min:0>2}:{self.sec:0>2}"
        

T0 = Time(0)
    

class Depth(Quantity):
    unit = Unit.make(m=1)


class Volume(Quantity):
    unit = Unit.make(m=3)
    fmt_unit = 'l'
    fmt_scale = 1e3


class VFR(Quantity):
    unit = Unit.make(m=3, s=-1)
    fmt_unit = 'l/min'
    fmt_scale = 60e3


class Pressure(Quantity):
    unit = Unit.make(m=-1, kg=1, s=-2)
    fmt_unit = 'bar'
    fmt_scale = 1e-5


class Density(Quantity):
    unit = Unit.make(m=-3, kg=1)
    fmt_unit = 'kg/m³'
    fmt_scale = 1


class Acceleration(Quantity):
    unit = Unit.make(m=1, s=-2)
    fmt_unit = 'm/s²'
    fmt_scale = 1
