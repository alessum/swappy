import numpy as np
import random as rd
import functions as fn
import itertools as itr
import scipy.special as spsp
import os

################################
# Delete old input files
################################

folder_path = "input_data/"
for file_name in os.listdir(folder_path):
    if file_name == "tasks_file.txt" or file_name[:10] == "parameters":
        file_path = os.path.join(folder_path, file_name)
        os.remove(file_path)

################################
# Set new input parameters
################################
# On my laptop
# T1000:
#       N16: 5s
#       N18: 16s
#       N20: 74s
#       N22: 342s

N = 14 # The number of spin-1/2 particles in the system
J_list = np.append(np.linspace(0.001,0.999*np.pi/2,17), np.pi-np.linspace(0.001,0.999*np.pi/2,17)[:-1][::-1])
J_list = [np.pi]
print(J_list)
Jz_list = [np.pi] # np.linspace(0.01,0.99*np.pi/4,20) #
    # The coefficient of the 2-q interaction
boundary_conditions = 'PBC' 
    # The chain boundary conditions, either 'PBC' or 'OBC'.
two_qubit_gate_ordering = 'brickwork' # 'random' # 
    
num_random_instances = 1
    # The number of disorder realisations
t_final = 1000 # for spin density computation
t_thresholds = 10, 100, 2**60 # for SFF computation
# The number of time-steps for the dynamics
magnetization = 0.5 if N%2 else 0.0  #np.arange(-(0.5*N)+1, (0.5*N)+1)]
    # magnetization symmetry subsector, i.e., value of $0.5\sum_n\sigma_n^z
D = spsp.binom(N, int(0.5*N + magnetization))
# Eigenphase target for POLFED algorithm
num_ev = min([int(D/10), 750])
# Number of eigphases/eigstates to return around phi_target in POLFED
num_cv = min([D, max([2*num_ev+1, 20])])
# Number of Lanczos vectors in POLFED. Must be greater than 2*n_ev.
k = int(0.8 * 2*D / num_cv) 
# Number of random initial states:
R = 1

for i, triplet in enumerate(itr.product(range(num_random_instances),
                                     J_list, Jz_list)):

    rd_idx, J, Jz = triplet
    rd_idx += 0
    parameter_id = f"N{N}_J{np.round(J,5)}_Jz{np.round(Jz,5)}" + \
                   f"_m{magnetization}" + \
                   f"_{boundary_conditions}" + \
                   f"_{two_qubit_gate_ordering}" + \
                   f"_idx{rd_idx:04d}" #_R{R}"
    parameter_id = parameter_id.replace(".",",")

    ################################

    params = {'N' : N,
              'J' : J,
              'Jz' : Jz,
              'magnetization' : magnetization,
              'boundary_conditions' : boundary_conditions,
              'two_qubit_gate_ordering' : two_qubit_gate_ordering,
              'compute_spin_density_dynamics' : False,
              'compute_spectral_form_factor' : False,
              't_final' : t_final,
              't_thresholds' : t_thresholds,
              'compute_eigvals_POLFED' : True,
              'compute_eigvec_entanglement_POLFED' : True,
              'compute_spectral_form_factor_POLFED': False,
              'phi_target' : 0,
              'k' : k,
              'num_ev' : num_ev,
              'num_cv' : num_cv,
              'parameter_id' : parameter_id,
              'num_random_initial_states': R,
              }

    ################################

    with open(f"input_data/parameters_{i:05d}.py", "w") as f:
        f.write("params = " + str(params))

    with open("input_data/tasks_file.txt", "a") as f:
        f.write("python write_to_file.py" +
                f" parameters_{i:05d}.py" + "\n")

