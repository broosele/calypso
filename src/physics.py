from .quantity import Acceleration, Density, Depth, Pressure


class Gas:
    def __init__(self, o2: float, he: float):
        self.o2 = o2
        self.he = he

    @property
    def n2(self) -> float:
        return 1 - self.o2 - self.he
    
    def __str__(self) -> str:
        if self.he == 0:
            if self.o2 == 0.21:
                return 'AIR'
            else:
                return f"EAN{int(100*self.o2)}"
        else:
            return f"TM{int(100*self.o2)}/{int(100*self.he)}"

    def ead(self, depth: float) -> float:
        return depth_from_pressure(pressure_from_depth(depth)*self.n2/AIR.n2)
    
    def ppo2(self, ambient_pressure: Pressure) -> Pressure:
        return self.o2*ambient_pressure
    
    def ppn2(self, ambient_pressure: Pressure) -> Pressure:
        return self.n2*ambient_pressure
    
    def pphe(self, ambient_pressure: Pressure) -> Pressure:
        return self.he*ambient_pressure
    
    
AIR = Gas(o2=0.21, he=0)


D_H2O = Density(1e3)
G = Acceleration(9.81)
P_ATM = Pressure(1013e2)
P_ALV_H2O = Pressure(6270)


def pressure_from_depth(depth: Depth) -> Pressure:
    return P_ATM + depth*(D_H2O*G)


def depth_from_pressure(pressure: Pressure) -> Depth:
    return (pressure - P_ATM)/(D_H2O*G)
