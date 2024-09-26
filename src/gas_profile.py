
from typing import Self
from .depth_profile import DepthProfile
from .gear import Cylinder
from .physics import P_ATM, Gas, pressure_from_depth
from .timeline import Timeline, TimeSegment
from .quantity import VFR, Pressure, Time


class GasUsage:
    def __init__(self, gas_supply_name: str, sac: VFR):
        self.gas_supply_name = gas_supply_name
        self.sac = sac

    
class GasUsageProfile:
    def __init__(self, timeline: Timeline, gas_usages: dict[TimeSegment, GasUsage]):
        self.timeline = timeline
        self.gas_usages = gas_usages

    def __getitem__(self, time: Time) -> GasUsage:
        return self.gas_usages[self.timeline.segment_for(time)]


class GasSupply:
    def __init__(self, cylinder: Cylinder, gas: Gas, pressure: Pressure):
        self.cylinder = cylinder
        self.gas = gas
        self.pressure = pressure

    def __str__(self) -> str:
        return f"{self.gas_volume_atm} of {self.gas}"

    @property
    def volume(self) -> float:
        return self.cylinder.volume

    @property
    def gas_volume_atm(self) -> float:
        return self.pressure/P_ATM*self.volume
    
    def consume(self, volume: float, pressure: float = P_ATM) -> Self:
        new_volume_atm = self.gas_volume_atm - pressure/P_ATM*volume
        new_pressure = new_volume_atm*P_ATM/self.volume
        return GasSupply(self.cylinder, self.gas, new_pressure)

    
class GasSupplySet:
    def __init__(self, **gas_supplies: dict[str, GasSupply]):
        self.gas_supplies = gas_supplies

    def __getitem__(self, gas_supply_name):
        return self.gas_supplies[gas_supply_name]

    def __str__(self) -> str:
        return ' | '.join(f"{name}: {gas_supply}" for name, gas_supply in self.gas_supplies.items())

    def consume(self, gas_supply_name: str, volume: float, pressure: float = P_ATM) -> Self:
        gas_supplies = {name: supply if name is not gas_supply_name else supply.consume(volume, pressure) for name, supply in self.gas_supplies.items()}
        return GasSupplySet(**gas_supplies)
    
    def use_for(self, segment: TimeSegment, depth, gas_usage: GasUsage) -> Self:
        volume = gas_usage.sac*segment.duration
        pressure = pressure_from_depth(depth)
        return self.consume(gas_supply_name=gas_usage.gas_supply_name, volume=volume, pressure=pressure)
        

class GasSupplyProfile:
    def __init__(self, timeline: Timeline, gas_supply_sets: dict[Time, GasSupplySet]):
        self.timeline = timeline
        self.gas_supply_sets = gas_supply_sets

    def __getitem__(self, time: Time) -> GasSupplySet:
        try:
            return self.gas_supply_sets[time]
        except KeyError:
            raise NotImplementedError()

    @staticmethod
    def create(start_gas_supply_set: GasSupplySet, depth_profile: DepthProfile, gas_usage_profile: GasUsageProfile) -> Self:
        timeline = depth_profile.timeline
        gas_supply_sets = {timeline[0]: start_gas_supply_set}
        for segment in timeline.segments:
            gas_supply_sets[segment.stop] = gas_supply_sets[segment.start].use_for(segment=segment, depth=depth_profile.average_depth(segment), gas_usage=gas_usage_profile[segment.start])
        return GasSupplyProfile(timeline=timeline, gas_supply_sets=gas_supply_sets)

