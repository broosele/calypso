import matplotlib.pyplot as plt

from .physics import depth_from_pressure

class DivePlot:
    def __init__(self, dive, deco):
        self.dive = dive
        self.deco = deco #probably not like this
        self._create()

    def _create(self):
        raise NotImplementedError()
    
    def show(self):
        pass


class ProfilePlot(DivePlot):
    def _create(self):
        time_values = [time.value/60 for time in self.dive.timeline]
        depth_values = [self.dive.depth_profile[t].value for t in self.dive.timeline]
        deco_values = {compartiment_name: [depth_from_pressure(state.n2_pressure).value for state in compartiment.states] for compartiment_name, compartiment in self.deco.profiles.items()}
        gas_supply_values = {
            gas_supply_name: [self.dive.gas_supply_profile[time].gas_supplies[gas_supply_name].pressure.value/1e5 for time in self.dive.timeline]
                for gas_supply_name in self.dive.start_gas_supply_set.gas_supplies
        }
        self._init_plot()
        self._plot_depth_profile(time_values, depth_values)
        self._plot_gas_supply_profile(time_values, gas_supply_values)
        self._plot_deco_profile(time_values, deco_values)


class MPLProfilePlot(ProfilePlot):
    def _init_plot(self):
        self.fig, self.axs = plt.subplots(2)
        self.fig.suptitle("Dive {self.dive.name}")
        tmax_value = self.dive.timeline[-1].value/60
        for ax in self.axs:
            ax.set_xlim([0, tmax_value])
            # ax.set_ylim(bottom=0)
            ax.grid()
        self.axs[0].set_title("depth profile")
        self.axs[0].set_ylabel("depth [m]")
        self.axs[0].yaxis.set_inverted(True)
        self.axs[1].set_title("gas supply")
        self.axs[1].set_xlabel("Time [min]")
        self.axs[1].set_ylabel("cylinder pressure [bar]")

    def _plot_depth_profile(self, time_values, depth_values):
        self.axs[0].plot(time_values, depth_values)

    def _plot_gas_supply_profile(self, time_values, gas_supply_values):
        for gas_supply_name in gas_supply_values:
            self.axs[1].plot(time_values, gas_supply_values[gas_supply_name], label=gas_supply_name)

    def _plot_deco_profile(self, time_values, deco_values):
        for compartiment_name in deco_values:
            self.axs[0].plot(time_values, deco_values[compartiment_name], label=compartiment_name)

    def show(self):
        self.axs[0].legend()
        self.axs[1].legend()
        plt.show()







# fig, axs = plt.subplots(3)
# fig.suptitle('Dive Profile')
# axs[0].plot(ts, ds)
# for i, compartiment_name in enumerate(d):
#     axs[0].plot(ts, [-depth_from_pressure(Pressure(pn2)).value for pn2 in d[compartiment_name]], label=compartiment_name, color=f'C{i}')
# axs[0].legend()
# for gas_supply_name in gas_supply_set.gas_supplies:
#     axs[1].plot(ts, ps[gas_supply_name], label=gas_supply_name)
# axs[1].legend()
# for i, compartiment_name in enumerate(d):
#     axs[2].plot(ts, d[compartiment_name], label=compartiment_name, color=f'C{i}')
#     axs[2].plot(ts, m[compartiment_name], '.', color=f'C{i}')
# axs[2].legend()
