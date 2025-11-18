
from turtle import color
import numpy as np
from sympy import im
import functions as fn
import matplotlib.pyplot as plt
import sys
import pandas as pd
import shutil
terminal_width, _ = shutil.get_terminal_size()
from matplotlib.colors import LinearSegmentedColormap
from scipy.special import binom

# import matplotlib
# matplotlib.use('QT5Agg')

colors = ["#394F87", "#A0B2E8", "#F0BCC1", "#7F0E0E", ]
cmapthree = LinearSegmentedColormap.from_list("custom_cmap", colors, N=256)

fn.begin()
time_elapsed = 0.0
############################################################################
tic = fn.tic("Loading data")
############################################################################

df = pd.read_csv(sys.argv[1:][0], comment="#")

#######################################
toc = fn.toc(tic)
time_elapsed += toc - tic
############################################################################
tic = fn.tic("Plotting data")
############################################################################

plt.rcParams['mathtext.fontset'] = 'cm'
#plt.rcParams["text.usetex"] = True
plt.rcParams["axes.linewidth"] = 1.5
plt.rcParams['text.latex.preamble']= r"\usepackage{amsmath}"

axis_label_fsize = 24
legend_fsize = 20
tick_label_fsize = 20

fig = plt.figure(figsize=(8,6))
ax = fig.add_subplot(1,1,1)

key = "N"
Nmax = 16
Nmin = 12
for i, N in enumerate(set(df[key].values)):
    color = cmapthree(i/(Nmax-Nmin))

    df_x = df[(df[key] == N)]

    J_list = df_x["J"].values
    J_z_list = df_x["Jz"].values
    gap_ratio_mean_list = df_x["gap_ratio_mean"].values
    gap_ratio_std_list = df_x["gap_ratio_std"].values
    #num_states_list = df_x["num_states"].values
    num_rd_instances_list = df_x["num_rd_instances"].values

    # operator_entanglement_list = np.array([fn.XXZ_gate_operator_entanglement(
    #     J_list[i],Delta_list[i]) for i in range(len(J_list))])

    #op_ent_list = [fn.s(J_list[i], J_list[i], Delta_list[i]*J_list[i])
    #               for i in range(len(J_list))]

    # idx = np.argsort(operator_entanglement_list)
    # operator_entanglement_list = operator_entanglement_list[idx]

    idx = np.argsort(J_list)
    J_list = J_list[idx]
    J_z_list = J_z_list[idx]
    gap_ratio_mean_list = gap_ratio_mean_list[idx]
    gap_ratio_std_list = gap_ratio_std_list[idx]
    num_rd_instances_list = num_rd_instances_list[idx]

    gap_ratio_error_list = np.divide(gap_ratio_std_list,
                                     np.sqrt(num_rd_instances_list))

    ax.errorbar((J_list - 0.0),# * x, #1 * np.log(x),
                gap_ratio_mean_list,
                # gap_ratio_mean_list / (0.5*x*np.log(2)),
                yerr=gap_ratio_error_list,
                capsize=3, marker='o', label=f"{key}={N}",
                color=color)
    #ax.errorbar(J_list * x, #/ (x * np.log(x)),
    #            gap_ratio_mean_list, yerr=gap_ratio_error_list,
    #            capsize=3, marker='x', label=f"{key}={x}")

    # ax.axhline(0.5*x*np.log(2) - 0.5)

ax.axhline(0.38629, ls='--', c='k') #, label='Poisson') # Poisson
ax.text(0.6,0.39,r'$\rm{Poisson}$',fontsize=axis_label_fsize)
ax.axhline(0.5307, ls='--', c='k') #, label='COE') # COE
ax.text(0.0,0.534,r'$\rm{COE}$',fontsize=axis_label_fsize)
ax.axhline(0.5996, ls='--', c='k') #, label='CUE') # COE
ax.text(0.0,0.602,r'$\rm{CUE}$',fontsize=axis_label_fsize)
ax.set_ylim([0.35, 0.65])
# ax.set_xlabel(r"$\mathcal{I} \cdot N$",fontsize=axis_label_fsize)
ax.set_xlabel(r"$J$",fontsize=axis_label_fsize)
ax.set_ylabel(r"$\langle \bar{r}$",
            #   r"$\langle \bar{S} \rangle / [(N/2)\log(2)]$",
              fontsize=axis_label_fsize)
ax.legend(fontsize=legend_fsize)
ax.tick_params(labelsize=tick_label_fsize)
plt.tight_layout()
plt.title(r'$\text{Gap ratio, }J_z=\pi/4$', y=1.05, fontsize=axis_label_fsize)
plt.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.15)

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

