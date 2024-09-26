
from functools import cache, cached_property
from typing import Self
from .depth_profile import DepthProfile
from .gas_profile import GasSupplySet, GasUsageProfile
from .physics import AIR, P_ALV_H2O, P_ATM, Gas, pressure_from_depth
from .quantity import Pressure, Time


class BMCompartiment:
    def __init__(self, name, halftime: Time, a: Pressure, b: float):
        self.name = name
        self.halftime = halftime
        self.a = a
        self.b = b

    @cache
    def agf(self, gf_low: float, gf_high: float, pressure_gf_low: Pressure) -> Pressure:
        return sum([
            (pressure_gf_low*gf_high - P_ATM*gf_low)/(pressure_gf_low - P_ATM)*self.a,
            pressure_gf_low*P_ATM/(pressure_gf_low - P_ATM)*(gf_high - gf_low)*(1-self.b)/self.b,
        ])

    @cache
    def bgf(self, gf_low: float, gf_high: float, pressure_gf_low: Pressure) -> float:
        return 1/sum([
            1,
            (gf_low - gf_high)/(pressure_gf_low - P_ATM)*self.a,
            (pressure_gf_low*gf_low - P_ATM*gf_high)/(pressure_gf_low - P_ATM)*(1-self.b)/self.b,
        ])


class BMCompartimentState:
    def __init__(self, compartiment: BMCompartiment, ambient_pressure: Pressure, n2_pressure: Pressure):
        self.compartiment = compartiment
        self.ambient_pressure = ambient_pressure
        self.n2_pressure = n2_pressure

    @property
    def m_value(self) -> Pressure:
        return self.compartiment.a + self.ambient_pressure/self.compartiment.b
    
    @property
    def gradient(self) -> Pressure:
        return self.n2_pressure - self.ambient_pressure
    
    @property
    def m_gradient(self) -> Pressure:
        return self.m_value - self.ambient_pressure
    
    @property
    def gradient_factor(self) -> float:
        return self.gradient/self.m_gradient
    
    # def gradient_factor_limit(self, gf_low: float, gf_high: float, pressure_gf_low: Pressure) -> float:
    #     return gf_high + (gf_low - gf_high)*(self.ambient_pressure - P_ATM)/(pressure_gf_low - P_ATM)
    
    def mgf_value(self, gf_low: float, gf_high: float, pressure_gf_low: Pressure) -> Pressure:
        return self.compartiment.agf(gf_low=gf_low, gf_high=gf_high, pressure_gf_low=pressure_gf_low) + self.ambient_pressure/self.compartiment.bgf(gf_low=gf_low, gf_high=gf_high, pressure_gf_low=pressure_gf_low)
        # return self.ambient_pressure + self.m_gradient*self.gradient_factor_limit(gf_low=gf_low, gf_high=gf_high, pressure_gf_low=pressure_gf_low)

    def next(self, duration: Time, ambient_pressure: Pressure, gas: Gas) -> Self:
        if duration > Time(10):
            raise NotImplementedError("Algorithm might not be accurate for timesteps lager than 10s. Who knows?")
        average_ambient_pressure = (self.ambient_pressure + ambient_pressure)/2
        n2_pressure = self.n2_pressure + (gas.ppn2(average_ambient_pressure - P_ALV_H2O) - self.n2_pressure)*(1 - 2**(-duration/self.compartiment.halftime))
        return BMCompartimentState(compartiment=self.compartiment, ambient_pressure=ambient_pressure, n2_pressure=n2_pressure)


class BMCompartimentProfile:
    def __init__(self, states: list[BMCompartimentState]):
        self.states = states

    @staticmethod
    def create(
            compartiment: BMCompartiment,
            depth_profile: DepthProfile, gas_usage_profile: GasUsageProfile,
            gas_supply_set: GasSupplySet, start_ambient_pressure: Pressure, start_n2_pressure: Pressure
        ) -> Self:
        states = [BMCompartimentState(compartiment=compartiment, ambient_pressure=start_ambient_pressure, n2_pressure=start_n2_pressure)]
        for segment in depth_profile.timeline.segments:
            duration = segment.duration
            ambient_pressure = pressure_from_depth(depth_profile[segment.stop])
            gas = gas_supply_set[gas_usage_profile[segment.start].gas_supply_name].gas
            states.append(states[-1].next(duration=duration, ambient_pressure=ambient_pressure, gas=gas))
        return BMCompartimentProfile(states)
    

class BMCompartimentProfiles:
    def __init__(self,
            compartiments: list[BMCompartiment], gf_low: float, gf_high: float, 
            depth_profile: DepthProfile, gas_usage_profile: GasUsageProfile,
            gas_supply_set: GasSupplySet, start_ambient_pressure: Pressure, start_n2_pressure: Pressure,
        ):
        self.profiles = {
            compartiment.name: BMCompartimentProfile.create(
                compartiment=compartiment,
                depth_profile=depth_profile, gas_usage_profile=gas_usage_profile,
                gas_supply_set=gas_supply_set, start_ambient_pressure=start_ambient_pressure, start_n2_pressure=start_n2_pressure,
            ) for compartiment in compartiments
        }
        self.gf_low = gf_low
        self.gf_high = gf_high

    def __getitem__(self, compartiment_name: str) -> BMCompartimentProfile:
        return self.profiles[compartiment_name]

    @cached_property
    def pressure_gf_low(self):
        return max(
            state.ambient_pressure
                for profile in self.profiles.values()
                    for state in profile.states
                        if state.gradient_factor > self.gf_low
        )


class Buhlmann:
    def __init__(self, compartiments: list[BMCompartiment], gf_low: float, gf_high: float):
        self.compartiments = compartiments
        self.gf_low = gf_low
        self.gf_high = gf_high
    
    def compartiment_profiles(self,
            depth_profile: DepthProfile, gas_usage_profile: GasUsageProfile,
            gas_supply_set: GasSupplySet, start_ambient_pressure: Pressure = P_ATM, start_n2_pressure: Pressure = AIR.ppn2(P_ATM),
        ) -> BMCompartimentProfiles:
        return BMCompartimentProfiles(
            compartiments=self.compartiments, gf_low=self.gf_low, gf_high=self.gf_high,
            depth_profile=depth_profile, gas_usage_profile=gas_usage_profile,
            gas_supply_set=gas_supply_set, start_ambient_pressure=start_ambient_pressure, start_n2_pressure=start_n2_pressure,
        )


def zh_l16c(gf_low: float, gf_high: float) -> Buhlmann:
    compartiments = [
        BMCompartiment(name=f"Compartiment {row+1}", halftime=Time(min=halftime), a=Pressure(a*1e5), b=b)
            for row, (halftime, a, b) in enumerate([
                (     5.0,  1.1696, 0.5578  ),
                (     8.0,  1.0000, 0.6514  ),
                (    12.5,  0.8618, 0.7222  ),
                (    18.5,  0.7562, 0.7825  ),
                (    27.0,  0.6200, 0.8126  ),
                (    38.3,  0.5043, 0.8434  ),
                (    54.3,  0.4410, 0.8693  ),
                (    77.0,  0.4000, 0.8910  ),
                (   109.0,  0.3750, 0.9092  ),
                (   146.0,  0.3500, 0.9222  ),
                (   187.0,  0.3295, 0.9319  ),
                (   239.0,  0.3065, 0.9403  ),
                (   305.0,  0.2835, 0.9477  ),
                (   390.0,  0.2610, 0.9544  ),
                (   498.0,  0.2480, 0.9602  ),
                (   635.0,  0.2327, 0.9653  ),
            ])
    ]
    return Buhlmann(compartiments=compartiments, gf_low=gf_low, gf_high=gf_high)
