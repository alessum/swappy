import numpy as np
import functions as fn
import scipy.special as spsp
import exact_diagonalization as ed
import pickle, timeit, sys, importlib, csv, shutil
terminal_width, _ = shutil.get_terminal_size()
import os.path as path

##########################################################################
fn.begin()
time_elapsed = 0.0
##########################################################################

N_list = [18]

for N in N_list:
    
    full_basis = range(2**N)
    m_list = [0.5] if N%2 else [0.0]  #np.arange(-(0.5*N)+1, (0.5*N)+1)]

    # Specify a subsystem for Schmidt numbers
    subsystem_site_indices = range(int(0.5*N))
    N_A = len(subsystem_site_indices)
    N_B = N - N_A
    
    for m in m_list:
        
        ###############################################################
        tic = fn.tic(f"Constructing block basis for N={N}, m={m}")
        ###############################################################

        block_basis = ed.magnetization_basis(full_basis, N, m)
        D = len(block_basis)

        #######################################
        toc = fn.toc(tic)
        time_elapsed += toc - tic
        ###############################################################
        tic = fn.tic(f"Building lookup vectors for N={N}, m={m}")
        ###############################################################

        # Create some of the vectors that encode the Floquet unitary
        qubit_i_up_mask = np.full((N,D), False, dtype=bool)
        qubits_ii1_same_mask = np.full((N,D), False, dtype=bool) 
        qubits_ii1_flip_reindexing = np.zeros((N,D))
        one_site_translation_reindexing = np.arange(D)

        # Create the vectors for efficient calculation of Schmidt numbers
        subsystem_num_zeros_idx_list = [[] for num_zeros in range(N_A + 1)]

        for j, state in enumerate(block_basis):

            int_input = isinstance(state, int)
            if int_input:
                "If state is an integer convert to corresponding bit string"
                state = bin(state)[2:].zfill(N)

            for i in range(N):

                if state[i] == '1':
                    qubit_i_up_mask[i,j] = True

                if state[i] == state[(i+1)%N]:
                    qubits_ii1_same_mask[i,j] = True
                else:
                    qubits_ii1_same_mask[i,j] = True

                    qubits_ii1_flipped_state = ed.flip_bits(state, [i,(i+1)%N], N)
                    qubits_ii1_flipped_state_idx = ed.find_in_sorted_list(
                        int(qubits_ii1_flipped_state,2), block_basis)
                    qubits_ii1_flip_reindexing[i,j] = qubits_ii1_flipped_state_idx

            translated_state = ed.translate_right(state, N)
            translated_state_idx = ed.find_in_sorted_list(
                int(translated_state,2), block_basis)
            one_site_translation_reindexing[j] = translated_state_idx

            # Generate the subsystem_num_zeros lookup vector (for Schmidt
            # numbers)
            subsystem_state = ''.join(state[n]
                                      for n in subsystem_site_indices)
            subsystem_state_num_zeros = subsystem_state.count("0")
            subsystem_num_zeros_idx_list[subsystem_state_num_zeros].append(j)

        #two_site_translation_reindexing = one_site_translation_reindexing[
        #    one_site_translation_reindexing]

        # Generate the reshape_dims_list lookup vector (for Schmidt
        # numbers)
        reshape_dims_list = []
        for num_zeros_A in range(N_A+1):
            m_A = 0.5*N_A - num_zeros_A
            m_B = m - m_A
            num_zeros_B = 0.5*N_B - m_B

            reshape_dims_list.append((int(spsp.binom(N_A, num_zeros_A)),
                                      int(spsp.binom(N_B, num_zeros_B))))

        #######################################
        toc = fn.toc(tic)
        time_elapsed += toc - tic
        #######################################
        tic = fn.tic(f"Saving Floquet vectors for N={N} and m={m}")
        ###############################################################

        floquet_lookup_data = [block_basis,
                           qubit_i_up_mask,
                           qubits_ii1_same_mask,
                           #qubits_01_differ_mask,
                           qubits_ii1_flip_reindexing,
                           one_site_translation_reindexing]

        subsystem_lookup_data = [subsystem_num_zeros_idx_list,
                                 reshape_dims_list]

        #################
        # Construct the path to the output directory
        #################
        p = path.normpath(__file__) # Find path to this file
        p = p.split(path.sep)[:-1]
            # Split the path into a list. Lose the .py file.
        output_dir_path = ['data_repos' if x=='code_repos' else x for x in p]
            # Replace 'code_repos' with 'data_repos' in the path list
        output_dir_path = output_dir_path + ['lookup_data']
            # Add the path to the lookup_files folder
        output_dir_path = '/' + path.join(*output_dir_path) + '/'
            # Join the list back into a path string
        output_subsystem_filename = f'N{N}_m{m}_NA{N_A}_subsystem_lookup_data'
        output_floquet_filename = f'N{N}_m{m}_floquet_lookup_data' # Whole system
        #################

        with open(output_dir_path + output_subsystem_filename, 'wb') as f:
                    pickle.dump(subsystem_lookup_data, f)

        with open(output_dir_path + output_floquet_filename, 'wb') as f:
                    pickle.dump(floquet_lookup_data, f)

        #######################################
        toc = fn.toc(tic)
        time_elapsed += toc - tic
        #######################################

#######################################
print('-' * terminal_width)
print('     Total runtime:', time_elapsed, 'seconds')
print('-' * terminal_width)
fn.finish()
#######################################
    
