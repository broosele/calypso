from functools import cached_property
import math
from typing import Iterator, Self

from .quantity import Time


# class TimePoint:
#     def __init__(self, time: Time):
#         self.time = time

#     def __str__(self) -> str:
#         return f"{self.time}"
    
#     def __hash__(self):
#         return hash((self.time,))
    
#     def __eq__(self, other: Self):
#         return self.time == other.time
    

# class MainTimePoint(TimePoint):
#     def __init__(self, time, name=None):
#         TimePoint.__init__(self, time=time)
#         self.name = name

#     def __str__(self) -> str:
#         if self.name is None:
#             return f"{self.time}"
#         else:
#             return f"{self.time} ({self.name})"


class TimeSegment:
    def __init__(self, start: Time, stop: Time):
        self.start = start
        self.stop = stop
    
    def __str__(self) -> str:
        f"{self.start}~{self.stop}"
    
    def __hash__(self):
        return hash((self.start, self.stop))
    
    def __eq__(self, other: Self) -> bool:
        return self.start == other.start and self.stop == other.stop
    
    def __contains__(self, time: Time) -> bool:
        return time >= self.start and time <= self.stop

    @property
    def duration(self) -> Time:
        return self.stop - self.start


class Timeline:
    def __init__(self, times: list[Time], named_times={}):
        self.times = times
        self.named_times = named_times

    def __getitem__(self, index: int) -> Time | Self:
        if isinstance(index, int):
            return self.times[index]
        else:
            times = self.times[index]
            named_times = {time: name for time, name in self.named_times.items() if time in times}
            return Timeline(times=times, named_times=named_times)
        
    def __iter__(self) -> Iterator[Time]:
        return iter(self.times)
    
    def __len__(self) -> int:
        return len(self.times)
    
    @cached_property
    def segments(self) -> list[TimeSegment]:
        return [TimeSegment(time0, time1) for time0, time1 in zip(self.times[:-1], self.times[1:])]

    @cached_property
    def named_profile(self) -> Self:
        return Timeline([time for time in self.times if time in self.named_times])
    
    def segment_for(self, time):
        for segment in self.segments:
            if time in segment:
                return segment
    
    def resample(self, sample_rate: Time):
        times = [self[0]]
        n = math.ceil(self[0]/sample_rate) + 1
        for existing_time in self[1:]:
            while (time := n*sample_rate) < existing_time:
                times.append(time)
                n += 1
            times.append(existing_time)
            n += 1
        return Timeline(times, named_times=self.named_times)
