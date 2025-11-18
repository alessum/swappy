from audioop import avg
import os, sys, re, pickle
import numpy as np
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from pyparsing import line
import scipy.special as scsp
from scipy.ndimage import gaussian_filter1d, uniform_filter1d
import heapq
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.colors import LinearSegmentedColormap

colors = ["#394F87", "#A0B2E8", "#F0BCC1", "#7F0E0E"]
cmap1 = LinearSegmentedColormap.from_list("custom_cmap", colors, N=256)
norm = plt.Normalize(vmin=0, vmax=np.pi)
smJ = plt.cm.ScalarMappable(cmap=cmap1, norm=norm)


if len(sys.argv[1:]) == 0:
    raise Exception("No input")
if len(sys.argv[1:]) >=1:
    N = sys.argv[1]
if len(sys.argv[1:]) >=2:
    t_max = int(sys.argv[2])
else:
    t_max = 10000
if len(sys.argv[1:]) >=3:
    num_bins = int(sys.argv[3])
else:
    num_bins = 15

redJvalues = np.array([1.55, 2.25])

directory = f'output/N{N}/C{t_max}/'

old_data = False
coeff = 4 if old_data else 1

N = int(N)
D = scsp.comb(N, N//2) # scsp.comb(N, N//2+1) if N%2 else 
# Initialize dictionary and Jvalues
if coeff == 1:
    Jvalues_original = np.append(np.linspace(0.001,0.999*np.pi/2,17), np.pi-np.linspace(0.001,0.999*np.pi/2,17)[:-1][::-1])[::]
else:
    Jvalues_original = np.append(np.linspace(0.001,0.999*np.pi/8,17), 
                             np.pi/4-np.linspace(0.001,0.999*np.pi/8,17)[:-1][::-1]
                             )[::]
Jvalues_original = np.append(Jvalues_original, np.pi/coeff)
# Jvalues_original = np.array([np.pi/coeff])
# Jvalues_original = np.append(Jvalues_original, .73)
Jvalues = (Jvalues_original * 1000).astype(int)
Jvalues = Jvalues.tolist()

Jvalues = np.array(Jvalues)
# print(Jvalues)
dic_values = {key: [] for key in Jvalues}

# Import each file
numb_rnd_instances = 0
for file_name in os.listdir(directory):
    if coeff == 1:
        if 'R' in file_name:
            continue
    else:
        if 'R' not in file_name:
            continue
    match = re.search(r'J(\d+),(...)', file_name)
    if match:
        key_int = int(match.group(1))
        key_dec = int(match.group(2))
        key = key_int * 1000 + key_dec
        with open(os.path.join(directory, file_name), 'rb') as f:
            try:
                dic_values[key].append(pickle.load(f))
            except:
                print('key not found', key, 'from', file_name, key_int, key_dec)
        numb_rnd_instances += 1

dic_values = {new_key: value for new_key, value in zip(Jvalues_original, dic_values.values())}

# Calculate averages
dic_avg_values = {}
for key, values in dic_values.items():
    if len(values) == 0:
        continue
    # [[params, t_list, JtJ0_list], [params, t_list, JtJ0_list], ...]
    #          disorder 0,                    disorder 1, ...
    t_list = np.array(values[0][1])
    numb_typical = min([values[i][2].shape[1] for i in range(len(values))])
    temp_data = np.array([np.average(values[i][2], axis=1)for i in range(len(values))])
    numb_disorder, _, _ = temp_data.shape
    # print(key*coeff, 'Dis =', numb_disorder, 'R =', numb_typical)
    # [JtJ0_list[t_ind][r][a], JtJ0_list[t_ind][r][a], ...]
    #      disorder 0,               disorder 1,       ...
    avg_values = np.average(temp_data[:,:,:].real, axis=(0))
    avg_values = np.sum(avg_values, axis=1) * D / N / np.pi
    dic_avg_values[key] = avg_values[1:]

# D = spsp.
# Prepare bins
t_list = t_list[1:]
log_t_list = np.log10(t_list)
bins = np.linspace(log_t_list.min(), log_t_list.max(), num_bins)
indices = np.digitize(log_t_list, bins)
avg_t_list = [t_list[indices == i].mean() for i in range(1, len(bins))]

# Prepare plot
fig = plt.figure(figsize=(20, 7))
gs = gridspec.GridSpec(1,3, figure=fig)

# Merge the first and third columns in both rows
ax = fig.add_subplot(gs[0]) 
ax1 = fig.add_subplot(gs[1]) 
ax2 = fig.add_subplot(gs[2]) 
inset_ax = inset_axes(ax2, width="50%", height="30%", loc=2)

for J, avg_values in dic_avg_values.items():

    colorJ = cmap1(J/np.pi*coeff)
    if min(np.abs(J*coeff-redJvalues))<.04:
        colorJ = 'r'
    # else:
    #     print(J*coeff, min(np.abs(J*coeff-redJvalues)))

    avg_avg_values = np.array([avg_values[indices == i].mean() for i in range(1, len(bins))])
    avg_values = gaussian_filter1d(uniform_filter1d(avg_values, size=5), sigma=2)
    t_list = gaussian_filter1d(uniform_filter1d(t_list, size=5), sigma=2)
    ax.plot(t_list[1:], avg_values[1:], linestyle='-', color=colorJ, alpha=.25) # marker='.', 
    # ax.plot(avg_t_list, np.array(avg_avg_values), marker='.', linestyle='-', label=f'J={J*coeff}', color=colorJ)


    # Apply the filter

    int_values = np.array([np.trapz(avg_values[:i], t_list[:i]) for i in range(1,len(t_list))])  # Step 3: Calculate the integral

    ax1.plot(t_list[1:], int_values, color=colorJ, alpha=.25)

    mask_values = []
    if np.abs(J*coeff) < 1.5:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]
    if np.abs(J*coeff-1.55) < 0.05:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]
    if np.abs(J*coeff-1.65) < 0.05:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]
    if np.abs(J*coeff-1.75) < 0.05:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]
    if np.abs(J*coeff-1.85) < 0.05:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]
    if np.abs(J*coeff-1.95) < 0.05:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]
    if np.abs(J*coeff-2.05) < 0.05:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]
    if np.abs(J*coeff-2.15) < 0.05:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]
    if np.abs(J*coeff-2.25) < 0.05:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]
    if np.abs(J*coeff-2.35) < 0.05:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]
    if np.abs(J*coeff-2.45) < 0.05:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]
    if np.abs(J*coeff-2.55) < 0.05:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]
    if np.abs(J*coeff-2.65) < 0.05:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]
    if np.abs(J*coeff-2.75) < 0.05:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]
    if np.abs(J*coeff-2.85) < 0.05:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]
    if np.abs(J*coeff-2.95) < 0.05:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]
    if np.abs(J*coeff-3.05) < 0.05:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]
    if np.abs(J*coeff-3.15) < 0.05:
        mask_begin = np.where(np.abs(t_list-9) < 1)[0][0]
        mask_end = np.where(np.abs(t_list-125) < 10)[0][0]
        mask_values = [np.arange(mask_begin, mask_end)]

    if len(mask_values) >= 1:
        mask1 = mask_values[0]
        t_list1, y_values1, y_values2 = t_list[1:][mask1], int_values[mask1], avg_values[1:][mask1]
        ax.plot(t_list1, y_values2, marker='.', linestyle='-', color=colorJ, alpha=1)
        ax1.plot(t_list1, y_values1, marker='.', linestyle='-', color=colorJ, alpha=1)
        extracted_coeff = np.trapz(y_values1, t_list1)/[t_list1[-1]-t_list1[0]]
        ax2.scatter(J*coeff, extracted_coeff, color=colorJ)
        inset_ax.scatter(J*coeff, np.trapz(y_values1, t_list1)/[t_list1[-1]-t_list1[0]], color=colorJ)
        inset_ax.axhline(0, linestyle='--', color='black', linewidth=.5)

inset_ax.set_xlim(-1e-2, 1.75)
inset_ax.set_ylim(-.05, .01)

inset_ax.tick_params(axis='both', which='major', labelsize=8)

ax1.plot(t_list[1:], t_list[1:]/1000, linestyle='--', color='black', linewidth=.5)
ax1.plot(t_list[1:], (t_list[1:]**.5)/1000, linestyle='-', color='black', linewidth=.5)
ax2.axhline(0, color='black', linestyle='--', linewidth=.5)

ax.set_xscale('log'); # ax.set_yscale('log')
ax1.set_xscale('log'); ax1.set_yscale('symlog')
ax1.set_ylim(-.15, 10000)
ax2.set_yscale('symlog')
ax2.set_ylim(-.1, 100)

# Configure colorbar
cbar = plt.colorbar(smJ, ax=ax2)
cbar.set_ticks(Jvalues_original * coeff)
cbar.set_ticklabels(np.round(Jvalues_original * coeff, 3))
cbar.set_label(r'$J$', labelpad=-20, y=-0.05, rotation=0)

red_Js = [min(Jvalues_original, key=lambda x: abs(x * coeff - target)) for target in redJvalues]
for red_J in red_Js:
    cbar.ax.axhline(red_J * coeff, color='red')

# Set labels and show plot
ax.set_title(f'N={N}, #circuits: {numb_disorder}, #states: >{numb_typical}')  # Add title
ax1.set_title(f'Coefficients v time')  # Add title
ax2.set_title(f'Averaged coefficient')  # Add title
# ax2.set_ylim(0,np.pi)

fig.suptitle(f'Analysis of J(t)J Correlation and Coefficients, data: {"Old" if old_data else "New"}', fontsize=16)

ax.set_xlabel('Time')
ax.set_ylabel(r'$\langle J(t)J \rangle$')
ax1.set_xlabel('Time')
ax1.set_ylabel(r'$\int_0^t \langle J(\tau)J \rangle d\tau$')
ax2.set_xlabel(r'$J$')
ax2.set_ylabel(r'$\int_0^t \langle J(\tau)J \rangle d\tau$')
plt.show()