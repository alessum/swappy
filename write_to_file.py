import numpy as np
import functions as fn
import random as rd
import numpy.random as nprd
# import scipy.linalg as la
import scipy.sparse.linalg as spla
import exact_diagonalization as ed
import pickle, sys, importlib, os, shutil #timeit, csv, 
import functools as ft
from tqdm import tqdm

# from numba import config
# # # set the threading layer before any parallel target compilation
# config.THREADING_LAYER_PRIORITY = ["omp", "tbb", "workqueue"]
# config.THREADING_LAYER = 'tbb'

verbosity = 1 # 0: returns nothing, 1: returns only total runtime, 2: returns partial runtimes

fn.begin(verbosity)
time_elapsed = 0.0
#########################################################################©#
tic = fn.tic("Importing parameters", verbosity)
##########################################################################

sys.path.insert(1, 'input_data')
if len(sys.argv[1:]) == 1:
    parameters = importlib.import_module(sys.argv[1][:-3])
    params = getattr(parameters, 'params')

params = getattr(parameters, 'params')

# for key, value in params.items():
#     globals()[key] = value
N = params['N']
J = params['J']
Jz = params['Jz']
boundary_conditions = params['boundary_conditions']
two_qubit_gate_ordering = params['two_qubit_gate_ordering']
magnetization = params['magnetization']
t_final = params['t_final']
compute_spin_density_dynamics = params['compute_spin_density_dynamics']
compute_spectral_form_factor = params['compute_spectral_form_factor']
compute_eigvals_POLFED = params['compute_eigvals_POLFED']
compute_eigvec_entanglement_POLFED = params['compute_eigvec_entanglement_POLFED']
compute_spectral_form_factor_POLFED = params.get('compute_spectral_form_factor_POLFED', False)
phi_target, k, = params['phi_target'], params['k'], 
num_ev, num_cv = params['num_ev'], params['num_cv']
parameter_id = params['parameter_id']
project_dir_path = os.path.dirname(__file__) 
output_folder = 'output/N'+ str(N) + '/T' + str(t_final)

# Check if the output folder exists
if not os.path.exists(output_folder) or not os.path.isdir(output_folder):
    raise Exception(f"The folder {output_folder} does not exist.")

if abs(magnetization) > 0.5*N:
    raise Exception(f"Magnetization |m|={abs(magnetization)} "+
                    f"shouldn't be bigger than N/2={0.5*N}")

#######################################
toc = fn.toc(tic, verbosity)
time_elapsed += toc - tic
######################################################################
tic = fn.tic("Building/loading vectors for Floquet evolution", verbosity)
######################################################################

# Load the lookup data with the info on the basis and the translation reindexing
lookup_file_name = f'N{N}_m{magnetization}_floquet_lookup_data'
with open(project_dir_path + '/lookup_data/' + lookup_file_name,
          'rb') as f:
    floquet_lookup_data = pickle.load(f)
block_basis, qubit_0_up_mask, qubits_01_same_mask, \
    qubits_01_flip_reindexing, one_site_translation_reindexing = floquet_lookup_data
D = len(block_basis)

# Generate the gates that will constitute the Unitary
h_list = nprd.uniform(-np.pi, np.pi, 4*N).reshape(-1, 4)
gates_parameters = [fn.gate_xxz_disordered(J, Jz, *h) for h in h_list]

# Generate the order the gates will be applied
if two_qubit_gate_ordering == 'random':
    if boundary_conditions == 'PBC':
        gate_ordering_idx_list = rd.sample([n for n in range(N)],N)
    elif boundary_conditions == 'OBC':
        gate_ordering_idx_list = rd.sample([n for n in range(N-1)],N-1)
elif two_qubit_gate_ordering == 'brickwork':
    gate_ordering_idx_list = []
    for n in range(N):
        if n % 2 == 0:
            if n == N-1 and boundary_conditions == 'OBC':
                continue
            else:
                gate_ordering_idx_list.append(n)
    for n in range(N):
        if n % 2 == 1:
            if n == N-1 and boundary_conditions == 'OBC':
                continue
            else:
                gate_ordering_idx_list.append(n)
gate_ordering_idx_list = np.array(gate_ordering_idx_list, dtype=int)
U_params = [gates_parameters, gate_ordering_idx_list]

#######################################
toc = fn.toc(tic, verbosity)
time_elapsed += toc - tic
######################################################################
tic = fn.tic("Computing translation reindexings", verbosity)
######################################################################

# Generate the translation reindexing lists
translation_reindexing = [np.arange(D), one_site_translation_reindexing]
temp = one_site_translation_reindexing
for n in range(N-2):
    temp = temp[one_site_translation_reindexing]
    translation_reindexing.append(temp)
translation_reindexing = np.array(translation_reindexing)
basis_data_for_U = [translation_reindexing, qubits_01_same_mask, 
                    qubit_0_up_mask, qubits_01_flip_reindexing]

#######################################
toc = fn.toc(tic, verbosity)
time_elapsed += toc - tic
######################################################################

if compute_spin_density_dynamics:
    ######################################################################
    tic = fn.tic("Computing spin density profile", verbosity)
    ######################################################################

    # Create psi_0: random pure state, with fully polarized n=0 qubit 
    psi_0 = nprd.normal(0,1,D) + 1.0j*nprd.normal(0,1,D)
    psi_0 = np.multiply(qubit_0_up_mask, psi_0)
    psi_0 = psi_0 / np.sqrt(np.dot(psi_0.conj(), psi_0))

    # Compute initial spin density profile
    spin_densities_0 = []
    qubit_n_up_mask = qubit_0_up_mask
    for n in range(N):
       spin_densities_0.append(np.dot(psi_0.conj(),
                                   np.multiply(2*qubit_n_up_mask-1,psi_0)))
       qubit_n_up_mask = qubit_n_up_mask[one_site_translation_reindexing]
    
    t_list = [0]
    spin_densities_list = [np.real(spin_densities_0)]
    psi_t = psi_0

    for t in tqdm(range(t_final+1)):
        # ######## APERIODIC DYNAMICS ########
        # gate_idx = nprd.randint(0, N)
        # gates_parameters = fn.gate_xxz_disordered(J, Jz, *nprd.uniform(-np.pi, np.pi, 4))
        # # Apply the 2-qubit gate
        # psi_t = psi_t[translation_reindexing[gate_idx]]
        # psi_t = fn.u_01(psi_t, gates_parameters, qubits_01_same_mask, 
        #                 qubit_0_up_mask, qubits_01_flip_reindexing)
        # psi_t = psi_t[translation_reindexing[(N - gate_idx) % N]]

        # # Compute spin density profile
        # spin_densities_t = []
        # qubit_n_up_mask = qubit_0_up_mask
        # for n in range(N):
        #     spin_densities_t.append(np.dot(psi_t.conj(),
        #                         np.multiply(2*qubit_n_up_mask-1,psi_t)))
        #     qubit_n_up_mask = qubit_n_up_mask[
        #         one_site_translation_reindexing]

        # t_list.append(t)
        # spin_densities_list.append(np.real(spin_densities_t))

        ####### PERIODIC DYNAMICS ########
        if t>100: old_gate_idx = 0 # For long time dynamics
        for order_idx, gate_idx in (enumerate(gate_ordering_idx_list)):
            # Apply the 2-qubit gate
            if t > 100:
                psi_t = psi_t[translation_reindexing[gate_idx - old_gate_idx]] 
            else:
                psi_t = psi_t[translation_reindexing[gate_idx]]
                
            psi_t = fn.u_01(psi_t, gates_parameters[gate_idx], qubits_01_same_mask, 
                            qubit_0_up_mask, qubits_01_flip_reindexing)
            if t > 100:
                old_gate_idx = gate_idx
                continue

            psi_t = psi_t[translation_reindexing[(N - gate_idx) % N]]
            # Compute spin density profile 
            spin_densities_t = []
            qubit_n_up_mask = qubit_0_up_mask
            for n in range(N):
                spin_densities_t.append(np.dot(psi_t.conj(),
                                    np.multiply(2*qubit_n_up_mask-1,psi_t)))
                qubit_n_up_mask = qubit_n_up_mask[
                    one_site_translation_reindexing]

            t_list.append(t + (order_idx+1)/len(gate_ordering_idx_list))
            spin_densities_list.append(np.real(spin_densities_t))

        if t > 100:
            psi_t = psi_t[translation_reindexing[-gate_ordering_idx_list[-1]]] 
            if (t>200   and t%2  !=0) or (t>500   and t%5  !=0) or (t>1000  and t%10 !=0) or \
               (t>2000  and t%20 !=0) or (t>5000  and t%50 !=0) or (t>10000 and t%100!=0) or \
               (t>20000 and t%200!=0) or (t>50000 and t%500!=0): continue
            # Compute spin density profile 
            spin_densities_t = []
            qubit_n_up_mask = qubit_0_up_mask
            for n in range(N):
                spin_densities_t.append(np.dot(psi_t.conj(),
                                    np.multiply(2*qubit_n_up_mask-1,psi_t)))
                qubit_n_up_mask = qubit_n_up_mask[
                    one_site_translation_reindexing]

            t_list.append(t)
            spin_densities_list.append(np.real(spin_densities_t))


    #######################################
    toc = fn.toc(tic, verbosity)
    time_elapsed += toc - tic
    ######################################################################
    tic = fn.tic("Saving spin density data", verbosity)
    ######################################################################

    spin_density_data = [params, t_list, spin_densities_list]

    with open(project_dir_path + '/' + output_folder + '/' + parameter_id +
                      '_spin_densities' , 'wb') as f:
                pickle.dump(spin_density_data, f)

    #######################################
    toc = fn.toc(tic, verbosity)
    time_elapsed += toc - tic
    #######################################

if compute_eigvals_POLFED:
    ######################################################################
    tic = fn.tic("Computing eigvals/eigvecs by POLFED", verbosity)
    ######################################################################

    # Define U as operator acting on a vector
    def U_floquet_matvec(psi):
        psi = psi.reshape((len(psi), ))
        return fn.U_floquet(psi, U_params, basis_data_for_U)
    
    U_floquet_LO = spla.LinearOperator((D,D), dtype=complex,
                                        matvec=U_floquet_matvec)

    inc = fn.increment_gen()

    # @njit(parallel=True, fastmath=True, cache=True)
    def g_k_matvec(psi):
        num_steps = next(inc)
        if not num_steps % 10:
            print('\rnum_steps:', num_steps, end='')
        return fn.g_evolution(psi, U_params, basis_data_for_U, phi_target, k)

    g_k_LO = spla.LinearOperator((D,D), dtype=complex, matvec=g_k_matvec)

    value = next(inc) - 1 
    print('call n°:', value, end='; ')
    eigvals_g_k_arnoldi, eigvecs_g_k_arnoldi = spla.eigs(g_k_LO, k=num_ev, ncv=num_cv)
    eigphases_g_k_arnoldi = np.angle(eigvals_g_k_arnoldi)

    #######################################
    toc = fn.toc(tic, verbosity)
    time_elapsed += toc - tic
    ######################################################################
    tic = fn.tic("Converting eigvals of g_k(U) to eigvals of U", verbosity)
    ######################################################################
    U_floquet_eigvecs_matmat = U_floquet_LO.matmat(eigvecs_g_k_arnoldi)

    eigvals_U_floquet_arnoldi = np.diag(eigvecs_g_k_arnoldi.T.conj() @
                                    U_floquet_eigvecs_matmat)
    eigphases_U_floquet_arnoldi = np.angle(eigvals_U_floquet_arnoldi)

    idx = np.argsort(eigphases_U_floquet_arnoldi)
    eigphases_U_floquet_arnoldi = eigphases_U_floquet_arnoldi[idx]
    eigphases_g_k_arnolid = eigphases_g_k_arnoldi[idx]
    eigvecs_g_k_arnoldi = eigvecs_g_k_arnoldi[:,idx]

    if not (compute_spectral_form_factor_POLFED and compute_eigvec_entanglement_POLFED):
        #######################################
        toc = fn.toc(tic, verbosity)
        time_elapsed += toc - tic
        ######################################################################
        tic = fn.tic("Saving eigvals data", verbosity)
        ######################################################################

        eigdata_arnoldi = [params, eigphases_U_floquet_arnoldi]
        with open(project_dir_path + '/' + output_folder + '/' + parameter_id + 
                        '_eigphases_POLFED' , 'wb') as f:
                    pickle.dump(eigdata_arnoldi[:2], f)
    
    if compute_spectral_form_factor_POLFED:
        #######################################
        toc = fn.toc(tic, verbosity)
        time_elapsed += toc - tic
        ###################################################################
        tic = fn.tic("Computing sff", verbosity)
        ###################################################################
        eigenergies_U_floquet_arnoldi = np.exp(-1j * eigphases_U_floquet_arnoldi)
        sff = [np.sum(np.abs(eigenergies_U_floquet_arnoldi**t)**2) for t in range(t_final+1)]
        #######################################
        toc = fn.toc(tic, verbosity)
        time_elapsed += toc - tic
        ######################################################################
        tic = fn.tic("Saving sff data", verbosity)
        ######################################################################

        eigdata_sff = [params, sff]
        with open(project_dir_path + '/' + output_folder + '/' + parameter_id + 
                        '_sff_POLFED' , 'wb') as f:
                    pickle.dump(eigdata_arnoldi[:2], f)
        

    if not compute_eigvec_entanglement_POLFED:
        #######################################
        toc = fn.toc(tic, verbosity)
        time_elapsed += toc - tic
        ######################################################################
        tic = fn.tic("Saving eigvals data", verbosity)
        ######################################################################

        eigdata_arnoldi = [params, eigphases_U_floquet_arnoldi]
        with open(project_dir_path + '/' + output_folder + '/' + parameter_id + 
                        '_eigphases_POLFED' , 'wb') as f:
                    pickle.dump(eigdata_arnoldi[:2], f)

    if compute_eigvec_entanglement_POLFED:
        #######################################
        toc = fn.toc(tic, verbosity)
        time_elapsed += toc - tic
        ###################################################################
        tic = fn.tic("Computing eigvec entanglement by POLFED", verbosity)
        ###################################################################

        subsystem_lookup_data_file_name = f'N{N}_m{magnetization}_'+\
            f'NA{int(0.5*N)}_subsystem_lookup_data'
        with open(project_dir_path + '/lookup_data/' +
                  subsystem_lookup_data_file_name,
                  'rb') as f:
            subsystem_lookup_data = pickle.load(f)

        subsystem_num_zeros_idx_list = subsystem_lookup_data[0]
        reshape_dims_list = subsystem_lookup_data[1]

        eigvec_entanglement_POLFED_list = []
        for eigvec in eigvecs_g_k_arnoldi.T:
            eigvec_schmidt_nums = ed.schmidt_nums_in_m_block(eigvec,
                                           subsystem_num_zeros_idx_list,
                                           reshape_dims_list)
            eigvec_entanglement_POLFED = 0
            for s in eigvec_schmidt_nums:
                if s == 0:
                    continue
                elif s < 0:
                    raise ValueError("Schmidt nums shouldn't be negative.")
                else:
                    eigvec_entanglement_POLFED += -s**2 * np.log(s**2)
                
            #eigvec_entanglement_ED = - sum(eigvec_schmidt_nums**2 *
            #                               np.log(eigvec_schmidt_nums**2))
            eigvec_entanglement_POLFED_list.append(
                eigvec_entanglement_POLFED)

        eigvec_entanglement_POLFED_data = [params,
                                           eigphases_U_floquet_arnoldi,
                                           eigvec_entanglement_POLFED_list]


        with open(project_dir_path + '/' + output_folder + '/' + parameter_id +
                          '_eigvec_entanglement_POLFED' , 'wb') as f:
                    pickle.dump(eigvec_entanglement_POLFED_data, f)

    #######################################
    toc = fn.toc(tic, verbosity)
    time_elapsed += toc - tic
    #######################################

#######################################
terminal_width, _ = shutil.get_terminal_size()

if verbosity!=0:
    print('-' * terminal_width)
    print('     Total runtime:', time_elapsed, 'seconds')
    print('-' * terminal_width)
fn.finish(verbosity)
#######################################
