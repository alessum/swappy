
from turtle import color
import numpy as np
import functions as fn
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.optimize as so
import pickle, sys, shutil
terminal_width, _ = shutil.get_terminal_size()
from tqdm import tqdm

# Maybe conserving SU(2) might be an interesting angle to take; wkbrillouin
fn.begin()
time_elapsed = 0.0
############################################################################
tic = fn.tic("Load data")
############################################################################

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

axis_label_fsize = 12
legend_fsize = 12
tick_label_fsize = 8

cmap = plt.colormaps.get_cmap('viridis') 
norm = plt.Normalize(vmin=-0, vmax=np.pi)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
Js = []

fig = plt.figure(figsize=(5.5,5))
ax = fig.add_subplot(1,1,1)

ax.set_title('Drift', fontsize=axis_label_fsize)
ax.set_xlabel('Time', fontsize=axis_label_fsize)
ax.set_ylabel('Drift', fontsize=axis_label_fsize)

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
    # index_100 = np.where(t_list == 100)[0][0]
    # t_list = t_list[:index_100]
    drift_list = np.array(data[2])
    std_drift_list = np.array(data[3])
    deviation_list = np.array(data[4])
    std_deviation_list = np.array(data[5])
            
    N = params['N']
    m = params['magnetization']
    
    
    J = params.get('J', params.get('Jxy', ''))*4
    if J == '':
        print(params)
    colorJ = sm.to_rgba(J)
    if J not in Js: Js.append(J)
    if  abs(J - 0.711028216656756*4) < .05:
        colorJ = 'red'
    if abs(J - 0.6621149188296278*4) < .05:
        colorJ = 'pink'
    
    plt.plot(drift_list, color=colorJ, linestyle='--', alpha=0.5)

    plt.axhline(np.mean(drift_list), color=colorJ, label='J = {}'.format(J))


cbar = plt.colorbar(sm, ax=ax)
cbar.set_ticks(Js)
cbar.set_ticklabels(np.round(np.array(Js), 3))
cbar.set_label(r'$J$', labelpad=-20, y=-0.05, rotation=0)
red_J = min(Js, key=lambda x: abs(x - 0.711028216656756*4))
pink_J = min(Js, key=lambda x: abs(x - 0.6621149188296278*4))
cbar.ax.axhline(pink_J, color='pink')
cbar.ax.axhline(red_J, color='red')
    
plt.show()

    
#######################################
toc = fn.toc(tic)
time_elapsed += toc - tic
#######################################
print('-' * terminal_width)
print('     Total:', time_elapsed, 'seconds')
print('-' * terminal_width)
fn.finish()
#######################################

plt.show()

