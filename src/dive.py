from typing import Self
from .quantity import T0, Time
from .depth_profile import DepthProfile
from .gas_profile import GasSupplyProfile, GasUsageProfile
from .timeline import Timeline


class Dive:
    def __init__(self,
            timeline: Timeline,
            depth_profile: DepthProfile,
            gas_usage_profile:GasUsageProfile,
            gas_supply_profile: GasSupplyProfile
        ):
        self.timeline = timeline
        self.depth_profile = depth_profile
        self.gas_usage_profile = gas_usage_profile
        self.gas_supply_profile = gas_supply_profile
        self.start_gas_supply_set = self.gas_supply_profile.gas_supply_sets[T0] #TODO: always T0?

    def resample(self, sample_period: Time) -> Self:
        timeline = self.timeline.resample(sample_period)
        depth_profile =  self.depth_profile.interpolate(timeline)
        gas_usage_profile = self.gas_usage_profile
        gas_supply_profile = GasSupplyProfile.create(
            start_gas_supply_set=self.start_gas_supply_set,
            depth_profile=depth_profile,
            gas_usage_profile=gas_usage_profile
        )
        return Dive(
            timeline=timeline,
            depth_profile=depth_profile,
            gas_usage_profile=gas_usage_profile,
            gas_supply_profile=gas_supply_profile,
        )
