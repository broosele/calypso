

# Dive plan
from ..src.buhlmann import zh_l16c
from ..src.dive_plan import DivePlan
from ..src.gas_profile import GasSupply, GasSupplyProfile, GasSupplySet
from ..src.gear import Cylinder
from ..src.physics import AIR, Gas, depth_from_pressure, pressure_from_depth
from ..src.quantity import Pressure, Time, Volume


EAN50 = Gas(o2=0.5, he=0)
main_cylinder = Cylinder(Volume(12e-3))
deco_cylinder = Cylinder(Volume(5.5e-3))
main = GasSupply(main_cylinder, AIR, Pressure(200e5))
deco = GasSupply(deco_cylinder, EAN50, Pressure(150e5))
start_gas_supply_set = GasSupplySet(main=main, deco=deco)


tec40_4 = [
    ( 0,  0.0, 'main', 20),
    ( 5,  1.0, 'main', 20),
    ( 5,  5.0, 'main', 20),
    (40,  3.0, 'main', 20),
    (40, 13.0, 'main', 20),
    (18,  2.5, 'deco', 20),
    (18,  1.0, 'deco', 15),
    ( 9,  1.0, 'deco', 15),
    ( 9,  0.5, 'deco', 15),
    ( 6,  0.5, 'deco', 15),
    ( 6,  1.5, 'deco', 15),
    ( 3,  0.5, 'deco', 15),
    ( 3,  2.5, 'deco', 15),
    ( 0,  0.5, 'deco', 15),
]


plan = DivePlan.from_table(start_gas_supply_set=start_gas_supply_set, table=tec40_4)


# Extracting values
timeline = plan.timeline.resample(Time(10))
depth_profile =  plan.depth_profile.interpolate(timeline)
gas_usage_profile = plan.gas_usage_profile
gas_supply_profile = GasSupplyProfile.create(start_gas_supply_set=start_gas_supply_set, depth_profile=depth_profile, gas_usage_profile=gas_usage_profile)
deco = zh_l16c(gf_low=0.35, gf_high=0.85).compartiment_profiles(depth_profile=depth_profile, gas_usage_profile=gas_usage_profile, gas_supply_set=start_gas_supply_set)


ts = [time.value/60 for time in timeline]
ds = [-depth_profile[t].value for t in timeline]
ps = {gas_supply_name: [gas_supply_profile[time].gas_supplies[gas_supply_name].pressure.value/1e5 for time in timeline] for gas_supply_name in start_gas_supply_set.gas_supplies}
d = {f"Compartiment {i+1}": [state.n2_pressure.value for state in deco[f"Compartiment {i+1}"].states] for i in range(8)}
m = {f"Compartiment {i+1}": [state.m_value.value for state in deco[f"Compartiment {i+1}"].states] for i in range(8)}
aps = [pressure_from_depth(depth_profile[t]).value for t in timeline]
mgf = {f"Compartiment {i+1}": [state.mgf_value(deco.gf_low, deco.gf_high, deco.pressure_gf_low).value for state in deco[f"Compartiment {i+1}"].states] for i in range(8)}

# Printing and plotting
for time, gas_supply_set in plan.gas_supply_profile.gas_supply_sets.items():
    print(f"{time}: {gas_supply_set}")


import matplotlib.pyplot as plt

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

n = 2
fig, axs = plt.subplots(n)
fig.suptitle('Compartiment loading')
for i in range(n):
    c = f"Compartiment {i+1}"
    axs[i].plot(aps, d[c], label='n2')
    axs[i].plot(aps, m[c], label='m')
    axs[i].plot(aps, mgf[c], label='mgf')
    axs[i].plot(aps, aps, label='Pamb')
    axs[i].plot(aps, [(mv-am)*0.35+am for mv, am in zip(m[c], aps)], label='mgf35')
    axs[i].plot(aps, [(mv-am)*0.85+am for mv, am in zip(m[c], aps)], label='mgf85')
    axs[i].grid()
    axs[i].legend()

plt.show()
