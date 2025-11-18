
import numpy as np
from sympy import im
import functions as fn
import matplotlib.pyplot as plt
import sys
import pandas as pd
import shutil
terminal_width, _ = shutil.get_terminal_size()

from scipy.special import binom

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

L_values = []
key = "N"
sorted_unique_x = sorted(df[key].unique())
for i, x in enumerate(sorted_unique_x):
    if x==10: #x == 10 or x == 18:
        continue
    else:
        # df_x = df[(df[key] == x) & (df["Jz"].between(np.pi/4*.99, np.pi/4*1.01)) & 
        #           (df["J"].between(0, np.pi/8*1.1))]
        df_x = df[(df[key] == x)]

    J_list = df_x["J"].values
    J_z_list = df_x["Jz"].values
    eigvec_entanglement_mean_list = df_x["eigvec_entanglement_mean"].values
    eigvec_entanglement_std_list = df_x["eigvec_entanglement_std"].values
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
    eigvec_entanglement_mean_list = eigvec_entanglement_mean_list[idx]
    eigvec_entanglement_std_list = eigvec_entanglement_std_list[idx]
    num_rd_instances_list = num_rd_instances_list[idx]

    eigvec_entanglement_error_list = eigvec_entanglement_std_list / (
                                     np.sqrt(num_rd_instances_list-1))

    ax.errorbar((J_list - 0.0),# * x, #1 * np.log(x),
                eigvec_entanglement_mean_list,
                # eigvec_entanglement_mean_list / (0.5*x*np.log(2)),
                yerr=eigvec_entanglement_error_list,
                capsize=3, marker='o', label=f"{key}={x}")
    #ax.errorbar(J_list * x, #/ (x * np.log(x)),
    #            gap_ratio_mean_list, yerr=gap_ratio_error_list,
    #            capsize=3, marker='x', label=f"{key}={x}")

    # ax.axhline(0.5*x*np.log(2) - 0.5)
    L_values.append(x)

#I* = b + a/N



# ax.set_xlabel(r"$\mathcal{I} \cdot N$",fontsize=axis_label_fsize)
ax.set_xlabel(r"$J$",fontsize=axis_label_fsize)
ax.set_ylabel(r"$\langle \bar{S} \rangle / S_{Page}$",
            #   r"$\langle \bar{S} \rangle / [(N/2)\log(2)]$",
              fontsize=axis_label_fsize)
ax.axhline(1, color='k', linestyle='--')
ax.axhline(0, color='k', linestyle='--')
ax.legend(fontsize=legend_fsize)
ax.tick_params(labelsize=tick_label_fsize)
plt.tight_layout()
plt.title(r'$\text{Entanglement entropy, }J_z=\pi/4$', y=1.05, fontsize=axis_label_fsize)
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


# ---------------- right panel: finite-size drift of crossing J* between L and L+2 ----------------
from scipy.interpolate import interp1d
from scipy.optimize import brentq
import math

fig, ax2 = plt.subplots(figsize=(6,5))

def find_crossing_J(J_vals, S1, S2):
    # Assumes J_vals sorted ascending
    J = np.array(J_vals)
    f1 = np.array(S1)
    f2 = np.array(S2)
    diff = f1 - f2
    sign = np.sign(diff)
    changes = np.where(sign[:-1] * sign[1:] <= 0)[0]
    if len(changes) == 0:
        return np.nan
    i = changes[0]  # take the first sign change
    J_left, J_right = J[i], J[i+1]
    f1_int = interp1d(J, f1, kind='linear', bounds_error=False, fill_value='extrapolate')
    f2_int = interp1d(J, f2, kind='linear', bounds_error=False, fill_value='extrapolate')
    try:
        root = brentq(lambda x: f1_int(x) - f2_int(x), J_left, J_right)
        return float(root)
    except ValueError:
        return np.nan

crossings = []
for L in sorted(L_values):
    Lp = L + 2
    if Lp not in L_values:
        continue

    df_L = df[df[key] == L]
    df_Lp = df[df[key] == Lp]
    if df_L.shape[0] < 2 or df_Lp.shape[0] < 2:
        continue

    J_union = np.unique(np.concatenate([df_L["J"].values, df_Lp["J"].values]))
    # Limit to J > .1 and J < .25
    J_union = J_union[(J_union > 0.05) & (J_union < .15)]
    J_union.sort()

    # interpolate normalized entropies onto union grid
    Snorm_L = interp1d(df_L["J"].values, df_L["eigvec_entanglement_mean"].values,
                       kind='linear', bounds_error=False, fill_value='extrapolate')(J_union)
    Snorm_Lp = interp1d(df_Lp["J"].values, df_Lp["eigvec_entanglement_mean"].values,
                        kind='linear', bounds_error=False, fill_value='extrapolate')(J_union)

    # find crossing J*
    J_star = find_crossing_J(J_union, Snorm_L, Snorm_Lp)

    # estimate error with simple bootstrap using SEM (if std/ninst exist)
    sem_L = interp1d(df_L["J"].values, df_L["eigvec_entanglement_std"].values / np.sqrt(np.maximum(df_L["num_rd_instances"].values,1)),
                     kind='linear', bounds_error=False, fill_value='extrapolate')(J_union)
    sem_Lp = interp1d(df_Lp["J"].values, df_Lp["eigvec_entanglement_std"].values / np.sqrt(np.maximum(df_Lp["num_rd_instances"].values,1)),
                      kind='linear', bounds_error=False, fill_value='extrapolate')(J_union)

    nboots = 300
    boot_roots = []
    for _ in range(nboots):
        pert_L = Snorm_L + np.random.normal(0, sem_L)
        pert_Lp = Snorm_Lp + np.random.normal(0, sem_Lp)
        r = find_crossing_J(J_union, pert_L, pert_Lp)
        boot_roots.append(r)
    boot_roots = np.array(boot_roots)
    boot_roots = boot_roots[~np.isnan(boot_roots)]
    if boot_roots.size == 0:
        J_err = np.nan
    else:
        J_err = np.nanstd(boot_roots)

    crossings.append((L, 1/L, J_star, J_err))
    crossings.append((L, L, J_star, J_err))

# plot crossings vs 1/L
if len(crossings) > 0:
    crossings = sorted(crossings, key=lambda x: x[1])  # sort by 1/L
    L_small = np.array([c[0] for c in crossings])
    invL = np.array([c[1] for c in crossings])
    Jstar = np.array([c[2] for c in crossings])
    Jerr = np.array([c[3] for c in crossings])

    ax2.errorbar(invL, Jstar, yerr=Jerr, fmt='o-', capsize=3)
    ax2.set_xlabel(r'$1/L$', fontsize=axis_label_fsize)
    ax2.set_ylabel(r'$J^\ast$ (crossing $ \langle \bar S\rangle / S_{Page}$ between $L$ and $L+2$)', fontsize=14)
    ax2.set_title('Finite-size drift of $J^*$ (for $0.05<J<0.15$)', fontsize=axis_label_fsize)
    ax2.tick_params(labelsize=tick_label_fsize)
else:
    ax2.text(0.5,0.5,'No crossings found (check data)', ha='center', va='center')
    ax2.set_axis_off()

plt.tight_layout()
plt.subplots_adjust(left=0.08, right=0.95, top=0.92, bottom=0.1)

toc = fn.toc(tic); time_elapsed += toc - tic
print('-' * terminal_width)
print('     Total:', time_elapsed, 'seconds')
print('-' * terminal_width)
fn.finish()

plt.show()

