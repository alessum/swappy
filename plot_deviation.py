
import numpy as np
import functions as fn
import matplotlib as mpl
import matplotlib.pyplot as plt
import pickle, sys, shutil
terminal_width, _ = shutil.get_terminal_size()
from tqdm import tqdm
from scipy.ndimage import uniform_filter1d, gaussian_filter1d
import heapq
from scipy.interpolate import splrep, splev


fn.begin()
time_elapsed = 0.0
############################################################################
tic = fn.tic("Load data")
############################################################################
drift_considered = True
redJvalues = np.array([2.05, 2.35])

data_list = []
if len(sys.argv[1:]) == 0:
    raise Exception("No data files were input")
elif len(sys.argv[1:]) > 0:
    for i in range(len(sys.argv[1:])):
        with open(sys.argv[1:][i], 'rb') as f:
            data_list.append(pickle.load(f))
    
#######################################
toc = fn.toc(tic)
time_elapsed += toc - tic
############################################################################
tic = fn.tic("Plot data")
############################################################################

axis_label_fsize = 14
legend_fsize = 14
tick_label_fsize = 10

t_list_max = [0]
import matplotlib.gridspec as gridspec

# Create a grid of 2x3 subplots
# fig = plt.figure(figsize=(10, 7))
# gs = gridspec.GridSpec(1, 1, figure=fig)
# ax = fig.add_subplot(gs[0, 0])


fig = plt.figure(figsize=(20, 9))
gs = gridspec.GridSpec(2, 3, figure=fig)

# Merge the first and third columns in both rows
ax1 = fig.add_subplot(gs[:, 0])
ax2a = fig.add_subplot(gs[0, 1])
ax2b = fig.add_subplot(gs[1, 1])
ax3 = fig.add_subplot(gs[:, 2])
ax = ax3
i = 0
avg_interval = 5
t_heis = 10
num_bins = 75


cmap = plt.colormaps.get_cmap('viridis')  # replace 'viridis' with your preferred colormap
norm = plt.Normalize(vmin=-0, vmax=np.pi)  # replace min_value and max_value with your actual min and max values
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
Js = []

for data in tqdm(data_list):
    
    #############################################
    # Load data
    #
    # Format
    #  - params                  data[0]
    #  - time_list               data[1]
    #  - drift_list              data[2]
    #  - std_drift_list          data[3]
    #  - deviation_list          data[4]
    #  - std_deviation_list      data[5]
    #############################################
    
    params = data[0]
    t_list = np.array(data[1])
    drift_list = np.array(data[2])
    std_drift_list = np.array(data[3])
    deviation_list = np.array(data[4])
    std_deviation_list = np.array(data[5])
    
    N = params['N']
    m = params['magnetization']
    n_list = range(N)

    # Prepare bins
    print('------94:------', t_list)
    t_list = t_list[1:]
    log_t_list = np.log10(t_list)
    bins = np.linspace(log_t_list.min(), log_t_list.max(), num_bins)
    indices = np.digitize(log_t_list, bins)
    avg_t_list = [t_list[indices == i].mean() for i in range(1, len(bins))]

    #############################################
    # Shift data so that perturbation appears in middle of
    # plots (shift = int(0.5 * N)), instead of edge (shift = 0)
    #############################################
    J = params.get('J', params.get('Jxy', ''))*4
    if J == '':
        print(params)
    colorJ = sm.to_rgba(J)
    if min(np.abs(J-redJvalues))<.05:
        colorJ = 'r'
    if J not in Js: Js.append(J)

    thres = 50000
    print('------114:------', t_list)
    stop = np.where(t_list > t_heis)[0][0]
    t_list_max = t_list_max if max(t_list[-1], t_list_max[-1])==t_list_max[-1] else t_list
        
    #############################################
    # Plot coefficients v time
    #############################################

    # Assuming t_list and p are your x and y data respectively
    D_values = np.array(deviation_list[1:])
    # t_list = np.array(t_list[10:])
    # avg_avg_values = [(D_values)[indices == i].mean() for i in range(1, len(bins))]
    # ax.plot(avg_t_list, avg_avg_values, ls='-', lw=1.5, color=colorJ, alpha=1) 

############################################################################################################
    # Apply the filter
    if J>.29:
        D_values = gaussian_filter1d(uniform_filter1d(D_values, size=20), sigma=5)
        t_list = gaussian_filter1d(uniform_filter1d(t_list, size=20), sigma=5)
    elif abs(J - .1) < .05:
        D_values = gaussian_filter1d(uniform_filter1d(D_values[1250:], size=200), sigma=10)
        t_list = gaussian_filter1d(uniform_filter1d(t_list[1250:], size=200), sigma=10)
    else:
        D_values = gaussian_filter1d(uniform_filter1d(D_values[50:], size=50), sigma=10)
        t_list = gaussian_filter1d(uniform_filter1d(t_list[50:], size=50), sigma=10)


    t_list_log = np.log(t_list)
    D_values_log = np.log(D_values)

    if J>2:
        k, s = 5, 10
    else:
        k, s = 5, .3
    f = splrep(t_list_log,D_values_log,k=k,s=s)
    der0_values = splev(t_list_log,f,der=0)
    der1_values = splev(t_list_log,f,der=1)
    der2_values = splev(t_list_log,f,der=2)
    ax2a.plot(t_list, der1_values, color=colorJ, alpha=.2)
    ax2b.plot(t_list, der2_values, color=colorJ, alpha=.2)
    ax.plot(t_list, der0_values, ls='-', lw=1.5, color=colorJ) 
    
    try:
        if abs(J-3.15)<0.05:
            mask_begin = np.where(np.abs(t_list-1) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-9) < .05)[0][0]
        if abs(J-3.05)<0.05:
            mask_begin = np.where(np.abs(t_list-1) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-9) < .05)[0][0]
        if abs(J-2.95)<0.05:
            mask_begin = np.where(np.abs(t_list-1) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-9) < .05)[0][0]
        if abs(J-2.85)<0.05:
            mask_begin = np.where(np.abs(t_list-1) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-9) < .05)[0][0]
        if abs(J-2.75)<0.05:
            mask_begin = np.where(np.abs(t_list-1) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-9) < .05)[0][0]
        if abs(J-2.65)<0.05:
            mask_begin = np.where(np.abs(t_list-1) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-9) < .05)[0][0]
        if abs(J-2.55)<0.05:
            mask_begin = np.where(np.abs(t_list-1) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-9) < .05)[0][0]
        if abs(J-2.45)<0.05:
            mask_begin = np.where(np.abs(t_list-1) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-9) < .05)[0][0]
        if abs(J-2.35)<0.05:
            mask_begin = np.where(np.abs(t_list-1) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-9) < .05)[0][0]
        if abs(J-2.25)<0.05:
            mask_begin = np.where(np.abs(t_list-1) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-9) < .05)[0][0]
        if abs(J-2.15)<0.05:
            mask_begin = np.where(np.abs(t_list-1) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-9) < .05)[0][0]
        if abs(J-2.05)<0.05:
            mask_begin = np.where(np.abs(t_list-1) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-9) < .05)[0][0]
        if abs(J-1.96)<0.02:
            mask_begin = np.where(np.abs(t_list-1) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-9) < .05)[0][0]
        if abs(J-1.86)<0.02:
            mask_begin = np.where(np.abs(t_list-1) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-9) < .05)[0][0]
        if abs(J-1.75)<0.02:
            mask_begin = np.where(np.abs(t_list-1) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-9) < .05)[0][0]
        if abs(J-1.65)<0.05:
            mask_begin = np.where(np.abs(t_list-1) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-9) < .05)[0][0]
        if abs(J-1.57)<0.01: # upwards still to set
            mask_begin = np.where(np.abs(t_list-1) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-9) < .05)[0][0]
        if abs(J-1.47)<0.01:
            mask_begin = np.where(np.abs(t_list-1.25) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-13) < .05)[0][0]
        if abs(J-1.37)<0.01:
            mask_begin = np.where(np.abs(t_list-1.85) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-20) < .05)[0][0]
        if abs(J-1.27)<0.01:
            mask_begin = np.where(np.abs(t_list-2.5) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-30) < .05)[0][0]
        if abs(J-1.17)<0.01:
            mask_begin = np.where(np.abs(t_list-4) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-50) < .05)[0][0]
        if abs(J-1.08)<0.01:
            mask_begin = np.where(np.abs(t_list-7) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-100) < .05)[0][0]
        if abs(J-0.98)<0.01:
            mask_begin = np.where(np.abs(t_list-11) < .5)[0][0]
            mask_end = np.where(np.abs(t_list-170) < 1)[0][0]
        if abs(J-0.88)<0.01:
            mask_begin = np.where(np.abs(t_list-17) < .5)[0][0]
            mask_end = np.where(np.abs(t_list-350) < 5)[0][0]
        if abs(J-0.78)<0.01:
            mask_begin = np.where(np.abs(t_list-29) < 1)[0][0]
            mask_end = np.where(np.abs(t_list-750) < 10)[0][0]
        if abs(J-0.68)<0.01:
            mask_begin = np.where(np.abs(t_list-45) < 5)[0][0]
            mask_end = np.where(np.abs(t_list-1500) < 10)[0][0]
        if abs(J-0.59)<0.01:
            mask_begin = np.where(np.abs(t_list-50) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-3000) < 10)[0][0]
        if abs(J-0.49)<0.01:
            mask_begin = np.where(np.abs(t_list-50) < .05)[0][0]
            mask_end = np.where(np.abs(t_list-3750) < 10)[0][0]
        if abs(J-0.39)<0.01:
            mask_begin = np.where(np.abs(t_list-110) < 1)[0][0]
            mask_end = -1
        if abs(J-0.30)<0.01:
            mask_begin = np.where(np.abs(t_list-115) < 1)[0][0]
            mask_end = -1
        if abs(J-0.20)<0.01:
            mask_begin = np.where(np.abs(t_list-150) < 1)[0][0]
            mask_end = -1
        if abs(J-0.10)<0.01:
            mask_begin = np.where(np.abs(t_list-240) < 1)[0][0]
            mask_end = -1
        if abs(J-0.00)<0.01:
            mask_begin = np.where(np.abs(t_list-150) < 1)[0][0]
            mask_end = -1
        print('mask_begin:', mask_begin, 'mask_end:', mask_end)
        print('t_list[mask_begin]:', t_list[mask_begin], 't_list[mask_end]:', t_list[mask_end])
        print('der1_values[mask_begin]:', der2_values[mask_begin], 'der1_values[mask_end]:', der2_values[mask_end])
        t_list1, y_values1, y_values2, y_values3 = \
        t_list[mask_begin:mask_end], der1_values[mask_begin:mask_end], \
            der0_values[mask_begin:mask_end], der2_values[mask_begin:mask_end]
        ax2a.plot(t_list1, y_values1, color=colorJ, linewidth=3)
        ax2b.plot(t_list1, y_values3, color=colorJ, linewidth=3)
        ax.plot(t_list1, y_values2, color=colorJ, linewidth=3)
        ax1.scatter(J, np.average(y_values1)/2, color=colorJ)
    except:
        continue
############################################################################################################

    i+=1   
print(Js)  

for t in t_list_max:
    if t==1 or (t % N == 0 and t < 10) or (t % 10 == 0 and t < 100) or \
    (t % 100 == 0 and t < 1000) or (t % 1000 == 0 and t < 10000):
        ax.axvline(t, c='k', lw = 0.1)
        # ax2a.axvline(t, c='k', lw = 0.1)
        # ax2b.axvline(t, c='k', lw = 0.1)

ax3.axhline(0, c='k', ls='--', lw=1)
ax3.axhline(33.2, c='k', ls='--', lw=1)
ax1.axhline(0, c='k', ls='--', lw=1)
ax1.axhline(1, c='k', ls='--', lw=1)
ax1.axhline(.5, c='k', ls='--', lw=1)
for J in Js:
    ax1.axvline(J, c='k', ls='--', lw=1, alpha=.2)
ax2a.axhline(1, c='k', ls='--', lw=1)
ax2a.axhline(0, c='k', ls='--', lw=1)
ax2b.axhline(-.5, c='k', ls='--', lw=1)
ax2b.axhline(.5, c='k', ls='--', lw=1)
ax2b.set_xlabel(r"${\rm Time,~} t$", fontsize=axis_label_fsize)

ax3.set_xlabel(r"${\rm Time,~} t$", fontsize=axis_label_fsize)
ax3.set_ylabel(r"$\gamma \langle \Delta (t) \rangle+\eta$",
                fontsize=axis_label_fsize)
# ax1.set_xlabel(r"$J$", fontsize=axis_label_fsize)
# ax1.set_ylabel(r"$b$", fontsize=axis_label_fsize)

ax3.set_title(f"Spatial deviation, $N={params['N']}$, $J_z=\pi$") # {params['Jz']:.4f}
ax2a.set_title(f"First (top) and Second (bottom) derivative") # {params['Jz']:.4f}
ax1.set_title(f"Exponents extracted from $\Delta^2(t)$") # {params['Jz']:.4f}
ax1.set_xlim(.5, 15000); # ax1.set_ylim(1.5/N, .55 * N)
ax1.set_xlim(-.25, 3.5); ax1.set_ylim(-.05, .55)
ax2a.set_xlim(.5, 15000); ax2a.set_ylim(-.15, 1.45)
ax2b.set_xlim(.5, 15000); ax2b.set_ylim(-1.2, 1.2)
ax3.set_xlim(.5, 15000); ax.set_ylim(3.e-3, 50)
if False: #drift_considered:
    fig.suptitle("Spatial deviation of the spin densities, considering the drift")
else:
    fig.suptitle("Spatial deviation of the spin densities")
ax3.set_xscale('log')
ax3.set_yscale('log')
ax2a.set_xscale('log')
ax2b.set_xscale('log')


if t_list_max[0] == 0:
    t_list_max = t_list_max[1:]
    
cbar = plt.colorbar(sm, ax=ax)
cbar.set_ticks(Js)
cbar.set_ticklabels(np.round(np.array(Js), 3)) #np.pi-
cbar.set_label(r'$J$', labelpad=-20, y=-0.05, rotation=0)
red_J = heapq.nsmallest(len(redJvalues), Js, key=lambda x: min(abs(x - redJvalues)))
for Jvalue in red_J:
    cbar.ax.axhline(Jvalue, color='red')

ax.plot(t_list, (np.array(t_list))/5, color='k', linestyle='--')

#######################################
toc = fn.toc(tic)
time_elapsed += toc - tic
#######################################
print('-' * terminal_width)
print('     Total:', time_elapsed, 'seconds')
print('-' * terminal_width)
fn.finish()
######################################

plt.show()

