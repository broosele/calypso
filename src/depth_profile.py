from typing import Self
from .timeline import Timeline, TimeSegment
from .quantity import Depth, Time


class DepthProfile:
    def __init__(self, timeline: Timeline, depths: dict[Time, Depth]):
        self.timeline = timeline
        self.depths = depths

    def __getitem__(self, time: Time) -> Depth:
        try:
            return self.depths[time]
        except KeyError:
            return self._interpolate_depth(self.timeline.segment_for(time), time)
    
    def average_depth(self, segment: TimeSegment) -> Depth:
        return (self.depths[segment.start] + self.depths[segment.stop])/2

    def _interpolate_depth(self, segment: TimeSegment, time: Time) -> Depth:
        time0 = segment.start
        time1 = segment.stop
        depth0 = self[segment.start]
        depth1 = self[segment.stop ]
        return ((depth0*(time1 - time) + depth1*(time - time0))/(time1 - time0))
    
    def interpolate(depth_profile: Self, timeline: Timeline) -> Self:
        depths = {}
        for time in timeline:
            depths[time] = depth_profile[time]
        return DepthProfile(timeline=timeline, depths=depths)
