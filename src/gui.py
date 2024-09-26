import matplotlib.pyplot as plt

class DivePlot:
    def __init__(self, dive):
        self.dive = dive
        self._create()

    def _create(self):
        raise NotImplementedError()
    
    def show(self):
        pass


class ProfilePlot(DivePlot):
    def _create(self):
        self.time_values = [time.value/60 for time in self.dive.timeline]
        self.depth = depth_profile[t].value for t in self.dive.timeline
        self._init_plot()
        self._plot_depth_profile()


class MPLProfilePlot(ProfilePlot):
    def _create(self):
        self.fig, self.axs = plt.subplots(3)
        fig.suptitle(f"Dive {self.dive.name}")

    def show(self):
        plt.show()







fig, axs = plt.subplots(3)
fig.suptitle('Dive Profile')
axs[0].plot(ts, ds)
for i, compartiment_name in enumerate(d):
    axs[0].plot(ts, [-depth_from_pressure(Pressure(pn2)).value for pn2 in d[compartiment_name]], label=compartiment_name, color=f'C{i}')
axs[0].legend()
for gas_supply_name in gas_supply_set.gas_supplies:
    axs[1].plot(ts, ps[gas_supply_name], label=gas_supply_name)
axs[1].legend()
for i, compartiment_name in enumerate(d):
    axs[2].plot(ts, d[compartiment_name], label=compartiment_name, color=f'C{i}')
    axs[2].plot(ts, m[compartiment_name], '.', color=f'C{i}')
axs[2].legend()
