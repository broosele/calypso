
from functools import cached_property

from .dive import Dive
from .depth_profile import DepthProfile
from .gas_profile import GasSupplyProfile, GasSupplySet, GasUsage, GasUsageProfile
from .quantity import T0, VFR, Depth, Time
from .timeline import Timeline


class DivePlanRow:
    def __init__(self, depth_m: int, duration_min: int, gas_supply_name: str, sac_lmin: int):
        self.depth = Depth(depth_m)
        self.duration = Time(min=duration_min)
        self.gas_supply_name = gas_supply_name
        self.sac = VFR(sac_lmin/60e3)


class DivePlan:
    def __init__(self, start_gas_supply_set: GasSupplySet, rows: list[DivePlanRow]):
        self.start_gas_supply_set = start_gas_supply_set
        self.rows = rows

    def __len__(self):
        return len(self.rows)
    
    def __iter__(self):
        return iter(self.rows) 
    
    @cached_property
    def dive(self) -> Dive:
        return Dive(
            timeline=self.timeline,
            depth_profile=self.depth_profile,
            gas_usage_profile=self.gas_usage_profile,
            gas_supply_profile=self.gas_supply_profile,
        )
    
    @cached_property
    def timeline(self):
        durations = [row.duration for row in self]
        times = [sum(durations[:n+1], T0) for n in range(len(self))]
        return Timeline(times, named_times={time: f"P{i}" for i, time in enumerate(times)})
    
    @cached_property
    def depth_profile(self):
        depths = {time: row.depth for time, row in zip(self.timeline, self)}
        return DepthProfile(timeline=self.timeline, depths=depths)
    
    @cached_property
    def gas_usage_profile(self):
        gas_usages = {segment: GasUsage(gas_supply_name=row.gas_supply_name, sac=row.sac) for segment, row in zip(self.timeline.segments, self)}
        return GasUsageProfile(timeline=self.timeline, gas_usages=gas_usages)
    
    @cached_property
    def gas_supply_profile(self):
        return GasSupplyProfile.create(start_gas_supply_set=self.start_gas_supply_set, depth_profile=self.depth_profile, gas_usage_profile=self.gas_usage_profile)

    @staticmethod
    def from_table(start_gas_supply_set, table):
        return DivePlan(start_gas_supply_set, [DivePlanRow(*row) for row in table])
    