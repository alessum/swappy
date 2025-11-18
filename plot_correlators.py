
import numpy as np
import functions as fn
import matplotlib as mpl
import matplotlib.pyplot as plt
# import pandas as pd
# import numpy.linalg as npla
# import scipy.linalg as la
import scipy.optimize as so
# import scipy.special as spsp
import pickle, sys
from tqdm import tqdm


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

# plt.rcParams['mathtext.fontset'] = 'cm'
# plt.rcParams["text.usetex"] = True
# plt.rcParams["axes.linewidth"] = 1.5
# plt.rcParams['text.latex.preamble']= r"\usepackage{amsmath}"

def modified_von_mises(n_list,kappa,alpha):
    von_mises = np.array([np.exp(kappa*np.cos(2*np.pi*(n-shift)/(N)))
                        for n in n_list])
    von_mises = von_mises - sum(von_mises)/len(von_mises) + 2*m/N
    von_mises = alpha * von_mises
    return von_mises


axis_label_fsize = 14
legend_fsize = 14
tick_label_fsize = 10

for data in tqdm(data_list):

    #############################################
    # Load data
    #############################################
    
    params = data[0]
    t_list = data[1]
    spin_densities_list = data[2]
    try:
        spin_densities_std_list = data[3]
    except:
        spin_densities_std_list = None
        
    N = params['N']
    m = params['magnetization']
    n_list = range(N)
    spin_densities_list = np.array(spin_densities_list)

    #############################################
    # Shift data so that perturbation appears in middle of
    # plots (shift = int(0.5 * N)), instead of edge (shift = 0)
    #############################################
    
    shift = int(0.5 * N)
    spin_densities_list = np.roll(spin_densities_list, shift, axis=1)


    #############################################
    # Plot slices at fixed position
    #############################################

    n_slice_list = [0]

    fig = plt.figure(figsize=(7,7))
    ax = fig.add_subplot(1,1,1)
    
    for n in n_slice_list:
        ax.plot(t_list, spin_densities_list[:,(n + shift)%N],
                marker='o', ls='-', fillstyle='none', lw=1,
                label=f"$n={n}$")

    for t_idx, t in enumerate(t_list):
        if t % 1 == 0:
            ax.axvline(t, c='k', lw = 0.1)
        
    ax.plot(t_list[1:], 0.15*np.array(t_list[1:])**(-0.5),
            label=r"$\sim t^{-1/2}$")
    ax.plot(np.array(t_list), 0.1*np.exp(-0.125*np.array(t_list)),
            label=r"$\sim e^{-at}$")

    ax.set_xlabel(r"${\rm Time,~} t$", fontsize=axis_label_fsize)
    ax.set_ylabel(r"$\langle \hat{\sigma}_n^z (t) \rangle$",
                  fontsize=axis_label_fsize)
        
    ax.set_xscale('log')
    ax.set_yscale('log')

    ax.legend(fontsize=legend_fsize)

    #############################################
    # Plot von Mises fitting parameters
    #############################################

    kappa_list = []
    alpha_list = []
    cov_list = []
    t_list = t_list[:]
    for t_idx, t in enumerate(t_list):
        try:
            p_opt, p_cov = so.curve_fit(modified_von_mises, n_list,
                                        spin_densities_list[t_idx])
            #print(t_idx, p_opt, p_cov)
            kappa_list.append(p_opt[0])
            alpha_list.append(p_opt[1])
            cov_list.append(np.trace(p_cov))
        except:
            kappa_list.append(None)
            alpha_list.append(None)
            cov_list.append(None)

    fig = plt.figure(figsize=(7,7))
    ax = fig.add_subplot(1,1,1)

    ax.plot(t_list[1:], kappa_list[1:], marker='.', label=r'$\kappa$')
    ax.plot(t_list[1:], alpha_list[1:], marker='.', label=r'$\alpha$')
    ax.plot(t_list[1:], cov_list[1:], marker='.', label=r'$Tr(C)$')
    ax.plot(t_list[1:], 3.0*np.array(t_list[1:])**(-2.0), c='k', lw=0.2,
            label=r"$t^{-2}$")

    ax.axhline(1/N, c='k', ls='--', lw=0.2, label=r"$1/N$")

    ax.set_xlabel(r"${\rm Time,~} t$", fontsize=axis_label_fsize)

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.legend(fontsize=legend_fsize)
    
#######################################
toc = fn.toc(tic)
time_elapsed += toc - tic
#######################################
print('-' * 78)
print('     Total:', time_elapsed, 'seconds')
print('-' * 78)
fn.finish()
#######################################

plt.show()

