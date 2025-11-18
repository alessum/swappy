
"""
This code is for exact diagonalisation of Hamiltonians with symmetries.
Mostly developed following the lecture notes by Anders W. Sandvik 
[AIP Conf. Proc. 1297, 135 (2010)].
"""

import numpy as np
import scipy.linalg as la
import scipy.sparse as sp
import scipy.special as spsp

######################################################################
# Useful state transformations
######################################################################

def translate_left(state, L):
    """
    Translate binary configuration one site to the left (assuming PBC),
    e.g., translate_left('0110100', 7) = '1101000'

    Input
    -----
    state : a binary string, e.g., '0110100', or the corresponding 
            decimal integer.

    L : an integer (the length of the binary string state).

    Output
    ------
    The binary string state translated one site to the left (or the 
    corresponding decimal integer).
    """
    if isinstance(state, str):
        "If the binary is written as a string of 0s and 1s."
        return state[1:] + state[0]
    elif isinstance(state, int):
        "If the binary is written as a decimal integer."
        return (2 * state) % (2**L) + int(state / 2**(L-1))

def translate_right(state, L):
    """
    Translate binary configuration one site to the right (assuming PBC),
    e.g., translate_right('0110100', 7) = '0011010'

    Input
    -----
    state : a binary string, e.g., '0110100', or the corresponding 
            decimal integer.

    L : an integer - the length of the binary string state.  

    Output
    ------
    The binary string state translated one site to the right (or the 
    corresponding decimal integer).  
    """
    if isinstance(state, str):
        "If the binary is written as a string of 0s and 1s."
        return state[-1] + state[:-1]
    elif isinstance(state, int):
        "If the binary is written as a decimal integer."
        return int(state / 2) + (state % 2) * 2**(L-1)

def reflect(state, L):
    """
    Reflect the binary configuration around the centre point, e.g.,
    reflect('1000', 4) = '0001' 
    reflect('10100',5) = '00101'

    Input
    -----
    state : a binary string, e.g., '0110100', or the corresponding 
            decimal integer.

    L : an integer - the length of the binary string state.  

    Output
    ------
    The binary string state reflected around the centre point (or the 
    corresponding decimal integer). 
    """
    if isinstance(state, str):
        "If the binary is written as a string of 0s and 1s."
        return state[::-1]
    elif isinstance(state, int):
        "If the binary is written as a decimal integer."
        return int((bin(state)[2:].zfill(L))[::-1], 2)

def flip_bits(state, indices, L):
    """
    Flip bits at `indices' in the bitstring state (indices run from 0 
    to L-1, where L is the number of bits in state). 
    """
    int_input = isinstance(state, int) #or isinstance(state, np.int64)
    if int_input:
        state = bin(state)[2:].zfill(L)

    flipped_state = state
    for i in indices:
        if flipped_state[i] == '0':
            flipped_state = flipped_state[:i] + '1' + flipped_state[i+1:]
        elif flipped_state[i] == '1':
            flipped_state = flipped_state[:i] + '0' + flipped_state[i+1:]

    if int_input:
        flipped_state = int(flipped_state, 2)

    return flipped_state

def raise_bits(state, indices, L):
    """
    Raise the bits at `indices' in the bitstring state (indices run from 
    0 to L-1, where L is the number of bits in state). 
    """
    int_input = isinstance(state, int)
    if int_input:
        state = bin(state)[2:].zfill(L)

    raised_state = state
    for i in indices:
        if raised_state[i] == '0':
            raised_state = raised_state[:i] + '1' + raised_state[i+1:]
        elif raised_state[i] == '1':
            raised_state = None
            break

    if int_input:
        raised_state = int(raised_state, 2)

    return raised_state

def lower_bits(state, indices, L):
    """
    Lower the bits at `indices' in the bitstring state (indices run from 
    0 to L-1, where L is the number of bits in state). 
    """
    int_input = isinstance(state, int)
    if int_input:
        state = bin(state)[2:].zfill(L)

    lowered_state = state
    for i in indices:
        if lowered_state[i] == '0':
            lowered_state = None
            break
        elif lowered_state[i] == '1':
            lowered_state = lowered_state[:i] + '0' + lowered_state[i+1:]

    if int_input:
        lowered_state = int(lowered_state, 2)

    return lowered_state
    
#######################################################################
# Other useful functions
#######################################################################

def representative(state, L, translations_only=False):
    """
    Given a state, return its `representative', the number of translations
    needed to get to the representative, and whether a reflection is
    necessary. 
    """
    if isinstance(state, str):
        "If state is a bit string, convert to corresponding integer."
        state = int(state, 2)

    representative = state
    num_translations = 0
    translated_state = state
    for i in range(1, L):
        translated_state = translate_right(translated_state, L)
        if translated_state < representative:
            representative = translated_state
            num_translations = i

    if translations_only == True:
        reflection = 0
    elif translations_only == False:
        reflection = 0
        translated_reflected_state = reflect(state, L)
        if translated_reflected_state < representative:
            representative = translated_reflected_state
            num_translations = 0
            reflection = 1
        for i in range(1, L):
            translated_reflected_state = \
                            translate_right(translated_reflected_state, L)
            if translated_reflected_state < representative:
                representative = translated_reflected_state
                num_translations = i
                reflection = 1

    return representative, num_translations, reflection

def find_in_sorted_list(x, sorted_integer_list):
    """
    Find the index of an integer x if it appears in the list of integers 
    sorted_integer_list. The list in sorted in increasing order. Done by 
    a bisectional search. Return the index as output. If x isn't in 
    sorted_integer_list, return -1.
    """

    if x < sorted_integer_list[0]:
        return -1
    elif x == sorted_integer_list[0]:
        return 0
    elif x > sorted_integer_list[-1]:
        return -1
    elif x == sorted_integer_list[-1]:
        return len(sorted_integer_list) - 1
    else:
        min_index = 0
        max_index = len(sorted_integer_list) - 1
        mid_index = min_index + int((max_index - min_index)/2.0)
        
        x_index = -1
        while min_index < mid_index and mid_index < max_index:
            if x < sorted_integer_list[mid_index]:
                max_index = mid_index
                mid_index = min_index + int((max_index - min_index)/2.0)
            elif x > sorted_integer_list[mid_index]:
                min_index = mid_index
                mid_index = min_index + int((max_index - min_index)/2.0)
            elif x == sorted_integer_list[mid_index]:
                x_index = mid_index
                break
            
        return x_index

def schmidt_nums(psi, d_A, d_B):
    """
    Given a pure state `psi' return its Schmidt numbers with respect to
    the bipartition into subsystems A and B.

    It is assumed that `psi' is a 1d row vector of dimension d_A x d_B, 
    where d_A is the dimension of subsystem A and d_B is the dimension of 
    subsystem B. 

    It is also assumed that the basis of `psi' is such that
    the numpy reshape function returns the tensor (i.e. numpy array) with
    its first index referring to the basis state of subsystem A, and the
    second index referring to the basis state of subsystem B.
    """
    
    psi = np.reshape(psi, (d_A, d_B))
    schmidt_nums = la.svd(psi, compute_uv=False)
    
    return schmidt_nums

def ent_entropy(psi, d_A, d_B):

    schmidt_nums_ = schmidt_nums(psi, d_A, d_B)

    ent_entropy = 0.0
    for i in range(len(schmidt_nums_)):
        lmda = schmidt_nums_[i]
        if lmda == 0:
            continue
        elif lmda < 0:
            raise ValueError("Schmidt numbers shouldn't be negative.")
        else:
            ent_entropy += -lmda**2 * np.log(lmda**2)
            
        #print('{}/{} done'.format(i, len(schmidt_nums_)))
                
    return ent_entropy   

#######################################################################
# Construct magnetization block basis
#######################################################################
    
def checkstate_magnetization(state, L):
    """ 
    Returns the magnetization of a computational basis state of spin-1/2
    particles. It is the number of up spins minus L/2 e.g.,

    checkstate_magnetization('000', 3) = -1.5
    checkstate_magnetization('100', 3) = -0.5
    checkstate_magnetization('110', 3) = 0.5
    checkstate_magnetization('111', 3) = 1.5

    Input
    -----
    state : a binary string, e.g., '0110100', or the corresponding 
            decimal integer.

    L : an integer - the length of the binary string state.  

    Output
    ------
    magnetization : an integer or half-integer.
    """
    if isinstance(state, int):
        "If state is a decimal integer convert to corresponding bitstring."
        state = bin(state)[2:].zfill(L)

    num_ones = state.count("1")
    magnetization = num_ones - 0.5 * L
    
    return magnetization

def magnetization_basis(basis, L, magnetization):
    """
    Given a basis, return the elements that have the allowed magnetization.
    """

    block_basis = []

    for state in basis:
        state_magnetization = checkstate_magnetization(state, L)
        if state_magnetization == magnetization:
            block_basis.append(state)

    return block_basis

def op_magnetization_block(L, m, block_basis, op_descriptor):

    dim = len(block_basis)
    basis_int_list = [int(state,2) for state in np.array(block_basis)]

    real_couplings = True
    for op_string, couplings in op_descriptor:
        coupling_strength = couplings[0][0]
        if np.imag(coupling_strength) != 0:
            real_couplings = False

    if real_couplings:
        dtype = np.float64
    elif not real_couplings:
        dtype = complex

    op_matrix = sp.lil_matrix((dim, dim), dtype=dtype)

    for j, state in enumerate(block_basis):

        int_input = isinstance(state, int)
        if int_input:
            "If state is an integer convert to corresponding bit string"
            state = bin(state)[2:].zfill(L)

        for op_string, couplings in op_descriptor:
        
            if op_string in ['x', 'y', '+', '-']:
                raise TypeError("Input operator descriptor doesn't" +
                                " conserve magnetization.")
            elif op_string == 'z':
                for coupling_strength, site_index in couplings:
                    op_matrix[j,j] += 2 * coupling_strength * \
                                      (int(state[site_index]) - 0.5)

            elif op_string == '1':
                # `1' is `up', not `down' here
                for coupling_strength, site_index in couplings:
                    op_matrix[j,j] += coupling_strength * \
                                      int(state[site_index])

            elif op_string == '0':
                # `0' is `down', not `up' here
                for coupling_strength, site_index in couplings:
                    op_matrix[j,j] += coupling_strength * \
                                      (1 - int(state[site_index]))

            elif op_string in ['xx', 'yy', 'xy', 'yx']:
                raise TypeError(f"Write operator descriptor {op_string} " +
                                "in terms of +'s and -'s instead")

            elif op_string == '+-':
                for coupling_strength, site_index_1, site_index_2 \
                    in couplings:
                    if (state[site_index_1] == '0' and
                        state[site_index_2] == '1'):
                        flipped_state = flip_bits(state,
                                                  [site_index_1,
                                                   site_index_2],L)
                        flipped_state_int = int(flipped_state,2)
                        i = find_in_sorted_list(flipped_state_int,
                                                basis_int_list)
                        op_matrix[i,j] += coupling_strength

            elif op_string == '-+':
                for coupling_strength, site_index_1, site_index_2 \
                    in couplings:
                    if (state[site_index_1] == '1' and
                        state[site_index_2] == '0'):
                        flipped_state = flip_bits(state,
                                                  [site_index_1,
                                                   site_index_2],L)
                        flipped_state_int = int(flipped_state,2)
                        i = find_in_sorted_list(flipped_state_int,
                                                basis_int_list)
                        op_matrix[i,j] += coupling_strength
                        
            elif op_string == 'zz':
                for coupling_strength, site_index_1, \
                    site_index_2 in couplings:
                    z1 = 2 * (int(state[site_index_1]) - 0.5)
                    z2 = 2 * (int(state[site_index_2]) - 0.5)
                    op_matrix[j,j] += coupling_strength * z1 * z2

            elif op_string == 'z+-':
                for coupling_strength, site_index_1, site_index_2, \
                    site_index_3 in couplings:
                    if (state[site_index_2] == '0' and
                        state[site_index_3] == '1'):
                        flipped_state = flip_bits(state,
                                                  [site_index_2,
                                                   site_index_3],L)
                        flipped_state_int = int(flipped_state,2)
                        i = find_in_sorted_list(flipped_state_int,
                                                basis_int_list)
                        op_matrix[i,j] += (coupling_strength * 2 *
                                           (int(state[site_index_1])-0.5))

            elif op_string == 'z-+':
                for coupling_strength, site_index_1, site_index_2, \
                    site_index_3 in couplings:
                    if (state[site_index_2] == '1' and
                        state[site_index_3] == '0'):
                        flipped_state = flip_bits(state,
                                                  [site_index_2,
                                                   site_index_3],L)
                        flipped_state_int = int(flipped_state,2)
                        i = find_in_sorted_list(flipped_state_int,
                                                basis_int_list)
                        op_matrix[i,j] += (coupling_strength * 2 *
                                           (int(state[site_index_1])-0.5))

            elif op_string == '+z-':
                for coupling_strength, site_index_1, site_index_2, \
                    site_index_3 in couplings:
                    if (state[site_index_1] == '0' and
                        state[site_index_3] == '1'):
                        flipped_state = flip_bits(state,
                                                  [site_index_1,
                                                   site_index_3],L)
                        flipped_state_int = int(flipped_state,2)
                        i = find_in_sorted_list(flipped_state_int,
                                                basis_int_list)
                        op_matrix[i,j] += (coupling_strength * 2 *
                                           (int(state[site_index_2])-0.5))

            elif op_string == '-z+':
                for coupling_strength, site_index_1, site_index_2, \
                    site_index_3 in couplings:
                    if (state[site_index_1] == '1' and
                        state[site_index_3] == '0'):
                        flipped_state = flip_bits(state,
                                                  [site_index_1,
                                                   site_index_3],L)
                        flipped_state_int = int(flipped_state,2)
                        i = find_in_sorted_list(flipped_state_int,
                                                basis_int_list)
                        op_matrix[i,j] += (coupling_strength * 2 *
                                           (int(state[site_index_2])-0.5))

            elif op_string == '+-z':
                for coupling_strength, site_index_1, site_index_2, \
                    site_index_3 in couplings:
                    if (state[site_index_1] == '0' and
                        state[site_index_2] == '1'):
                        flipped_state = flip_bits(state,
                                                  [site_index_1,
                                                   site_index_2],L)
                        flipped_state_int = int(flipped_state,2)
                        i = find_in_sorted_list(flipped_state_int,
                                                basis_int_list)
                        op_matrix[i,j] += (coupling_strength * 2 *
                                           (int(state[site_index_3])-0.5))

            elif op_string == '-+z':
                for coupling_strength, site_index_1, site_index_2, \
                    site_index_3 in couplings:
                    if (state[site_index_1] == '1' and
                        state[site_index_2] == '0'):
                        flipped_state = flip_bits(state,
                                                  [site_index_1,
                                                   site_index_2],L)
                        flipped_state_int = int(flipped_state,2)
                        i = find_in_sorted_list(flipped_state_int,
                                                basis_int_list)
                        op_matrix[i,j] += (coupling_strength * 2 *
                                           (int(state[site_index_3])-0.5))

    return op_matrix


def m_block_subsystem_basis_data(N, m, subsystem_site_indices,
                                 block_basis):
    """
    A sub-routine needed to calculate the Schmidt numbers of an N-qubit
    quantum state in a magnetisation sub-block (specified by m and by
    block_basis), with respect to some bipartition (specified by
    subsystem_site_indices).
    
    Inputs
    ------
    N : int
        The number of qubits in the system
    m : integer or half-integer between -0.5*N and +0.5*N
        The total magnetization that specifies the sub-block
    subsystem_site_indices : list of integers
        The list of site indices (between 0 and N-1) that specify a
        subsystem of qubits.
    block_basis : list of integers (or the corresponding binary strings)
        The block_basis corresponding to a magnetization sub-block

    Outputs
    -------
    subsystem_num_zeros_idx_list : a list of lists

        - The zero'th list gives the indices of the block_basis elements
          for which the subsystem has ZERO qubits in the "0" state.
        - The first list gives the indices of the block_basis elements for
          which the subsystem has ONE qubit in the "0" state.
        - ...
        - The len(subsystem_site_indices)'th list gives the indices of the
          block_basis elements for which the subsystem has ALL qubits
          in the "0" state.

    reshape_dims_list : list of couples
        The is a list of the same length as subsystem_num_zeros_idx_list.
        The i'th element of the list is a couple of reshape dimensions
        (d_A, d_B) that tells us how to reshape the vector indices
        given in subsystem_num_zeros_idx_list[i].
    
    """

    N_A = len(subsystem_site_indices)
    N_B = N - N_A

    subsystem_num_zeros_idx_list = [[] for num_zeros in range(N_A+1)]
    
    for idx, state in enumerate(block_basis):
        state_str = bin(state)[2:].zfill(N)
        subsystem_state_str = ''.join(state_str[n]
                                      for n in subsystem_site_indices)
        subsystem_state_num_zeros = subsystem_state_str.count("0")
        subsystem_num_zeros_idx_list[
            subsystem_state_num_zeros].append(idx)

    reshape_dims_list = []
    for num_zeros_A in range(N_A+1):
        m_A = 0.5*N_A - num_zeros_A
        m_B = m - m_A
        num_zeros_B = 0.5*N_B - m_B

        reshape_dims_list.append((int(spsp.binom(N_A, num_zeros_A)),
                                  int(spsp.binom(N_B, num_zeros_B))))

    return subsystem_num_zeros_idx_list, reshape_dims_list

def schmidt_nums_in_m_block(psi, subsystem_num_zeros_idx_list,
                            reshape_dims_list):
    """
    Calculates the Schmidt numbers of an N-qubit state psi in a
    magnetization sub-block.

    Requires the precalculated lists subsystem_num_zeros_idx_list and
    reshape_dims_list, which I assume were previously generated using the
    sub-routine m_block_subsystem_basis_data. These list contain all
    data on the bipartition etc.

    Inputs
    ------
    psi : 1-d array
        The vector for the quantum state
    subsystem_num_zeros_idx_list : list of lists
        A list of len(subsystem_site_indices)+1 lists.
        - The zero'th list gives the indices of the block_basis elements for
          which the subsystem has ZERO qubits in the "0" state.
        - The first list gives the indices of the block_basis elements for
          which the subsystem has ONE qubit in the "0" state.
        - ...
        - The len(subsystem_site_indices)'th list gives the indices of the
          block_basis elements for which the subsystem has ALL qubits
          in the "0" state.
    reshape_dims_list : list of couples
        The is a list of the same length as subsystem_num_zeros_idx_list.
        The i'th element of the list is a couple of reshape dimensions
        (d_A, d_B) that tells us how to reshape the vector indices
        given in subsystem_num_zeros_idx_list[i].

    Output
    ------
    schmidt_nums_list : 1-d array
       The Schmidt numbers of psi corresponding to the bipartition.
        
    """

    if len(psi) != sum([len(num) for num in subsystem_num_zeros_idx_list]):
        raise Exception("Dimensions of psi and "+
                        "subsystem_num_zeros_idx_list don't match."+
                        "Are you using the correct subsystem basis data?")

    schmidt_nums_list = np.array([])
    for num_zeros_A, indices in enumerate(subsystem_num_zeros_idx_list):

        reshape_dims = reshape_dims_list[num_zeros_A]
        
        psi_segment = psi[indices]
        psi_segment = np.reshape(psi_segment, reshape_dims)

        schmidt_nums_list = np.concatenate((schmidt_nums_list,
                                            la.svd(psi_segment,
                                                   compute_uv=False)))
        
    return schmidt_nums_list

        
######################################################################
# Construct momentum block basis
######################################################################
    
def checkstate_momentum(state, L, k):
    """ 
    This is the subroutine to check if a state should be included in the 
    list of representatives of the momentum basis with momentum k and, 
    if so, to return its periodicity. 

    Here k is an integer in the range 
        
        -L/2 + 1,..., L/2

    and it really represents the momentum eigenvalue 2*pi*k/L.

    (See Sandvik2010 pg. 66, or In. [9] at
    http://lptms.u-psud.fr/membres/groux/Test/ED/ED_Lecture2.html)
    """

    if isinstance(state, str):
        "If state is a bit string, convert to corresponding integer."
        state = int(state, 2)

    if L % 2 == 0 and (k > int(L/2) or k < -int(L/2) + 1):
        raise ValueError("k is out of range")
    elif L % 2 == 1 and abs(k) > int(L/2):
        raise ValueError("k is out of range")

    translated_state = state
    for i in range(L):
        translated_state = translate_right(translated_state, L)
        if translated_state < state:
            return -1
        elif translated_state == state:
            if (k % (L/(i+1))) != 0:
                return -1
            else:
                return i + 1

def momentum_basis_reps(basis, L, k):
    """
    Given some basis, return elements that are representatives of momentum
    eigenstates with momentum 2*pi*k/L, along with the corresponding 
    periodicity of the representative.

    (See Sandvik2010LectureNotes, section 4.1.3.)
    """

    reps = []
    
    for state in basis:
        periodicity = checkstate_momentum(state, L, k)
        if periodicity > 0:
            reps.append((state, periodicity))
            
    return reps

def op_momentum_block_general(L, k, basis_reps, op_descriptor):
    """
    Returns the matrix for an operator (specified by `op_descriptor') in 
    the k-momentum block, and in the momentum basis specified by 
    `basis_reps'.

    *** The operator must be translationally invariant, i.e., it must 
    commute with the translation operator. ***

    Input
    -----
    L : int
        The number of spin-half particles.
    k : int between -L/2+1 and L/2 
        The momentum block. The integer k really represents the momentum
        2*pi*k/L.
    basis_reps : list or array
        The list of integer representatives of the basis for the block.
    op_descriptor : list
        The list that specifies the operator. Each element of the
        list is itself a list of the form [op_string, couplings], where
        `op_string' is a string representing an operator, and `couplings'
        specifies the sites on which the operator acts, as well as the
        coupling constant.

        For example, for the operator O=\sum_{i=0}^{L-1} w \sigma_i^z
        we have op_descriptor = [["z", [[w, i] for i in range(L)]]].

        For two-site operators op_list looks like, e.g.,
        op_descriptor = [["zz", [[w, i, i+1] for i in range(L-1)]]].

        See [SciPost Phys. 2, 003 (2017)] section 2.1 for more details.

    """

    dim = len(basis_reps)
    basis_reps_int_list = [int(state,2) for state in
                           np.array(basis_reps)[:,0]]

    if L % 2 == 0 and (k > int(L/2) or k < -int(L/2) + 1):
        raise ValueError("k is out of range")
    elif L % 2 == 1 and abs(k) > int(L/2):
        raise ValueError("k is out of range")

    real_couplings = True
    for op_string, couplings in op_descriptor:
        coupling_strength = couplings[0][0]
        if (np.imag(coupling_strength) != 0) or \
           (op_string.count('y') % 2 == 1):
            real_couplings = False

    if k == 0 or abs(k) == int(L/2) == L/2:
        if real_couplings:
            dtype = np.float64
        elif not real_couplings:
            dtype = complex
    else:
        dtype = complex

    op_matrix = sp.lil_matrix((dim, dim), dtype=dtype)

    for j in range(dim):
        
        state_rep_j, R_j = basis_reps[j]

        for op_string, coupling_list in op_descriptor:

            # CHECK TRANSLATION INVARIANCE
            
            # if (len(op_string) == 1 and
            #     (len(np.array(couplings)[:,1]) != L or
            #     set(np.array(couplings)[:,1]) != set(range(L)))):
            #     raise TypeError("Input operator is not translationally" +
            #                     "invariant.")
            # if len(set(np.array(couplings)[:,0])) > 1:
            #     raise TypeError("Input operator is not translationally" +
            #                     "invariant.")

            for coupling in coupling_list:
                
                coupling_strength = coupling[0]
                site_indices = coupling[1:]

                x_indices = [site_indices[i] for i, op_char in
                             enumerate(op_string) if op_char == 'x']
                y_indices = [site_indices[i] for i, op_char in
                             enumerate(op_string) if op_char == 'y']
                z_indices = [site_indices[i] for i, op_char in
                             enumerate(op_string) if op_char == 'z']

                op_matrix_element = coupling_strength

                if len(y_indices + z_indices) > 0:
                    
                    if isinstance(state_rep_j, int):
                        state_rep_j = bin(state_rep_j)[2:].zfill(L)
                    
                    y_factor = 1
                    for y_index in y_indices:
                        if state_rep_j[y_index] == '0':
                            y_factor *= -1.0j
                        else:
                            y_factor *= +1.0j
                    if np.imag(y_factor) == 0:
                        y_factor = np.real(y_factor)
                 
                    z_factor = 1
                    for z_index in z_indices:
                        if state_rep_j[z_index] == '0':
                            z_factor *= -1

                    op_matrix_element *= y_factor * z_factor

                if len(x_indices + y_indices) > 0:

                    flipped_state = flip_bits(state_rep_j,
                                              x_indices + y_indices, L)
                    state_rep_i, num_translations = \
                           representative(flipped_state, L,
                                          translations_only=True)[:2]
                    i = find_in_sorted_list(state_rep_i,
                                              basis_reps_int_list)
                        # this is the flipped_state_rep index
                    R_i = basis_reps[i][1]
                    if i >= 0:
                        if k == 0 or abs(k) == int(L/2) == L/2:
                            op_matrix_element *= (np.sqrt(R_j/R_i) *
                                       np.real(np.exp(2.0j*np.pi*
                                                num_translations*k/L)))
                        else:
                            op_matrix_element *= (np.sqrt(R_j/R_i) *
                                 np.exp(2.0j*np.pi*num_translations*k/L))
                    elif i < 0:
                        op_matrix_element = 0

                    del flipped_state

                    op_matrix[i,j] += op_matrix_element

                elif len(x_indices + y_indices) == 0:

                    op_matrix[j,j] += op_matrix_element

    return op_matrix


def op_momentum_block(L, k, basis_reps, op_descriptor):
    """
    Returns the matrix for an operator (specified by `op_descriptor') in 
    the k-momentum block, and in the momentum basis specified by 
    `basis_reps'.

    *** The operator must be translationally invariant, i.e., it must 
    commute with the translation operator. ***

    Input
    -----
    L : int
        The number of spin-half particles.
    k : int between -L/2+1 and L/2 
        The momentum block. The integer k really represents the momentum
        2*pi*k/L.
    basis_reps : list or array
        The list of integer representatives of the basis for the block.
    op_descriptor : list
        The list that specifies the operator. Each element of the
        list is itself a list of the form [op_string, couplings], where
        `op_string' is a string representing an operator, and `couplings'
        specifies the sites on which the operator acts, as well as the
        coupling constant.

        For example, for the operator O=\sum_{i=0}^{L-1} w \sigma_i^z
        we have op_descriptor = [["z", [[w, i] for i in range(L)]]].

        For two-site operators op_list looks like, e.g.,
        op_descriptor = [["zz", [[w, i, i+1] for i in range(L-1)]]].

        See [SciPost Phys. 2, 003 (2017)] section 2.1 for more details.

    """

    dim = len(basis_reps)
    basis_reps_int_list = [int(state,2) for state in
                           np.array(basis_reps)[:,0]]

    if L % 2 == 0 and (k > int(L/2) or k < -int(L/2) + 1):
        raise ValueError("k is out of range")
    elif L % 2 == 1 and abs(k) > int(L/2):
        raise ValueError("k is out of range")

    real_couplings = True
    for op_string, couplings in op_descriptor:
        coupling_strength = couplings[0][0]
        if (np.imag(coupling_strength) != 0) or \
           (op_string.count('y') % 2 == 1):
            real_couplings = False

    if k == 0 or abs(k) == int(L/2) == L/2:
        if real_couplings:
            dtype = np.float64
        elif not real_couplings:
            dtype = complex
    else:
        dtype = complex

    op_matrix = sp.lil_matrix((dim, dim), dtype=dtype)

    for j in range(dim):
        
        state_rep_j, R_j = basis_reps[j]

        for op_string, couplings in op_descriptor:
            if (len(op_string) == 1 and
                (len(np.array(couplings)[:,1]) != L or
                set(np.array(couplings)[:,1]) != set(range(L)))):
                raise TypeError("Input operator is not translationally" +
                                "invariant.")
            if len(set(np.array(couplings)[:,0])) > 1:
                raise TypeError("Input operator is not translationally" +
                                "invariant.")
            
            if op_string == 'x':
                for coupling_strength, site_index in couplings:
                    flipped_state = flip_bits(state_rep_j, [site_index], L)
                    state_rep_i, num_translations = \
                           representative(flipped_state, L,
                                          translations_only=True)[:2]
                    i = find_in_sorted_list(state_rep_i,
                                              basis_reps_int_list)
                        # this is the flipped_state_rep index
                    R_i = basis_reps[i][1]
                    if i >= 0:
                        if k == 0 or abs(k) == int(L/2) == L/2:
                            op_matrix[i,j] += (coupling_strength *
                                               np.sqrt(R_j/R_i) *
                        np.real(np.exp(2.0j*np.pi*num_translations*k/L)))
                        else:
                            op_matrix[i,j] += (coupling_strength *
                                               np.sqrt(R_j/R_i) *
                                 np.exp(2.0j*np.pi*num_translations*k/L))

            elif op_string == 'y':
                for coupling_strength, site_index in couplings:
                    raised_state = raise_bits(state_rep_j, [site_index], L)
                    if raised_state != None:
                        flipped_state = raised_state
                        sigma_y_factor = -1.0j
                    elif raised_state == None:
                        flipped_state = lower_bits(state_rep_j,
                                                   [site_index], L)
                        sigma_y_factor = +1.0j

                    state_rep_i, num_translations = \
                               representative(flipped_state, L,
                                              translations_only=True)[:2]
                    i = find_in_sorted_list(state_rep_i,
                                        basis_reps_int_list)
                            # this is the flipped_state_rep index
                    R_i = basis_reps[i][1]
                    if i >= 0:
                        if k == 0 or abs(k) == int(L/2) == L/2:
                            op_matrix[i,j] += (sigma_y_factor *
                                    coupling_strength * np.sqrt(R_j/R_i)*
                        np.real(np.exp(2.0j*np.pi*num_translations*k/L)))
                        else:
                            op_matrix[i,j] += (sigma_y_factor *
                                    coupling_strength * np.sqrt(R_j/R_i)*
                            np.exp(2.0j*np.pi*num_translations*k/L))
            
            elif op_string == 'z':
                coupling_strength = couplings[0][0]
                op_matrix[j,j] += 2.0 * coupling_strength * \
                                  checkstate_magnetization(state_rep_j,L)

            elif op_string == '1':
                # `1' is `up', not `down' here
                op_matrix[j,j] += coupling_strength * (0.5 * L +
                                checkstate_magnetization(state_rep_j,L))

            elif op_string == '0':
                # `0' is `down', not `up' here
                op_matrix[j,j] += coupling_strength * (0.5 * L -
                                checkstate_magnetization(state_rep_j,L))

            elif op_string == 'xx':
                for (coupling_strength, site_index_1, site_index_2) in \
                    couplings:
                    flipped_state = flip_bits(state_rep_j,
                                            [site_index_1,site_index_2], L)
                    state_rep_i, num_translations = \
                           representative(flipped_state, L,
                                          translations_only=True)[:2]
                    i = find_in_sorted_list(state_rep_i,
                                              basis_reps_int_list)
                        # this is the flipped_state_rep index
                    R_i = basis_reps[i][1]
                    if i >= 0:
                        if k == 0 or abs(k) == int(L/2) == L/2:
                            op_matrix[i,j] += (coupling_strength *
                                               np.sqrt(R_j/R_i) *
                        np.real(np.exp(2.0j*np.pi*num_translations*k/L)))
                        else:
                            op_matrix[i,j] += (coupling_strength *
                                               np.sqrt(R_j/R_i) *
                                 np.exp(2.0j*np.pi*num_translations*k/L))

            elif op_string == 'yy':
                for (coupling_strength, site_index_1, site_index_2) in \
                    couplings:
                    
                    raised_site_1 = raise_bits(state_rep_j,
                                               [site_index_1], L)
                    if raised_site_1 != None:
                        flipped_state = raised_site_1
                        factor_site_1 = -1.0j
                    elif raised_site_1 == None:
                        flipped_state = lower_bits(state_rep_j,
                                                   [site_index_1], L)
                        factor_site_1 = +1.0j

                    raised_site_2 = raise_bits(flipped_state,
                                              [site_index_2], L)
                    if raised_site_2 != None:
                        flipped_state = raised_site_2
                        factor_site_2 = -1.0j
                    elif raised_site_2 == None:
                        flipped_state = lower_bits(flipped_state,
                                                   [site_index_2], L)
                        factor_site_2 = +1.0j

                    factor = np.real(factor_site_1 * factor_site_2)

                    state_rep_i, num_translations = \
                               representative(flipped_state, L,
                                              translations_only=True)[:2]
                    i = find_in_sorted_list(state_rep_i,
                                        basis_reps_int_list)
                            # this is the flipped_state_rep index
                    R_i = basis_reps[i][1]
                    if i >= 0:
                        if k == 0 or abs(k) == int(L/2) == L/2:
                            op_matrix[i,j] += (factor *
                                    coupling_strength * np.sqrt(R_j/R_i)*
                        np.real(np.exp(2.0j*np.pi*num_translations*k/L)))
                        else:
                            op_matrix[i,j] += (factor *
                                    coupling_strength * np.sqrt(R_j/R_i)*
                            np.exp(2.0j*np.pi*num_translations*k/L))

            elif op_string == 'zz':
                if isinstance(state_rep_j, int):
                    state_rep_j = bin(state_rep_j)[2:].zfill(L)
                for (coupling_strength, site_index_1,
                    site_index_2) in couplings:

                    zz_value = (-1)**(int(state_rep_j[site_index_1]) +
                                      int(state_rep_j[site_index_2]))
                    op_matrix[j,j] += coupling_strength * zz_value

            elif op_string == '+-':
                for (coupling_strength, site_index_1, site_index_2) in \
                    couplings:

                    flipped_state = raise_bits(state_rep_j,
                                               [site_index_1], L)
                    if flipped_state != None:
                        flipped_state = lower_bits(flipped_state,
                                               [site_index_2], L)
                   
                    i = -1
                    if flipped_state != None:
                        state_rep_i, num_translations = \
                                   representative(flipped_state, L,
                                                translations_only=True)[:2]
                        i = find_in_sorted_list(state_rep_i,
                                            basis_reps_int_list)
                                # this is the flipped_state_rep index
                        R_i = basis_reps[i][1]
                    if i >= 0:
                        if k == 0 or abs(k) == int(L/2) == L/2:
                            op_matrix[i,j] += (factor *
                                    coupling_strength * np.sqrt(R_j/R_i)*
                        np.real(np.exp(2.0j*np.pi*num_translations*k/L)))
                        else:
                            op_matrix[i,j] += (factor *
                                    coupling_strength * np.sqrt(R_j/R_i)*
                            np.exp(2.0j*np.pi*num_translations*k/L))

            elif op_string == '-+':
                for (coupling_strength, site_index_1, site_index_2) in \
                    couplings:

                    flipped_state = lower_bits(state_rep_j,
                                               [site_index_1], L)
                    if flipped_state != None:
                        flipped_state = raise_bits(flipped_state,
                                               [site_index_2], L)

                    i = -1
                    if flipped_state != None:
                        state_rep_i, num_translations = \
                                   representative(flipped_state, L,
                                                translations_only=True)[:2]
                        i = find_in_sorted_list(state_rep_i,
                                            basis_reps_int_list)
                                # this is the flipped_state_rep index
                        R_i = basis_reps[i][1]
                        
                    if i >= 0:
                        if k == 0 or abs(k) == int(L/2) == L/2:
                            op_matrix[i,j] += (factor *
                                    coupling_strength * np.sqrt(R_j/R_i)*
                        np.real(np.exp(2.0j*np.pi*num_translations*k/L)))
                        else:
                            op_matrix[i,j] += (factor *
                                    coupling_strength * np.sqrt(R_j/R_i)*
                            np.exp(2.0j*np.pi*num_translations*k/L))

            elif op_string == 'xz':
                if isinstance(state_rep_j, int):
                    state_rep_j = bin(state_rep_j)[2:].zfill(L)
                    
                for (coupling_strength, site_index_1, site_index_2) \
                    in couplings:

                    z_value = (-1)**(int(state_rep_j[site_index_2]) + 1)
                    
                    flipped_state = flip_bits(state_rep_j,[site_index_1],L)
                    state_rep_i, num_translations = \
                           representative(flipped_state, L,
                                          translations_only=True)[:2]
                    i = find_in_sorted_list(state_rep_i,
                                              basis_reps_int_list)
                        # this is the flipped_state_rep index
                    R_i = basis_reps[i][1]
                    if i >= 0:
                        if k == 0 or abs(k) == int(L/2) == L/2:
                            op_matrix[i,j] += (coupling_strength * z_value *
                                               np.sqrt(R_j/R_i) *
                        np.real(np.exp(2.0j*np.pi*num_translations*k/L)))
                        else:
                            op_matrix[i,j] += (coupling_strength * z_value *
                                               np.sqrt(R_j/R_i) *
                                    np.exp(2.0j*np.pi*num_translations*k/L))

            elif op_string == 'zx':
                if isinstance(state_rep_j, int):
                    state_rep_j = bin(state_rep_j)[2:].zfill(L)
                
                for (coupling_strength, site_index_1, site_index_2) \
                    in couplings:

                    z_value = (-1)**(int(state_rep_j[site_index_1]) + 1)
                    
                    flipped_state = flip_bits(state_rep_j,[site_index_2],L)
                    state_rep_i, num_translations = \
                           representative(flipped_state, L,
                                          translations_only=True)[:2]
                    i = find_in_sorted_list(state_rep_i,
                                              basis_reps_int_list)
                        # this is the flipped_state_rep index
                    R_i = basis_reps[i][1]
                    if i >= 0:
                        if k == 0 or abs(k) == int(L/2) == L/2:
                            op_matrix[i,j] += (coupling_strength * z_value *
                                               np.sqrt(R_j/R_i) *
                        np.real(np.exp(2.0j*np.pi*num_translations*k/L)))
                        else:
                            op_matrix[i,j] += (coupling_strength * z_value *
                                               np.sqrt(R_j/R_i) *
                                    np.exp(2.0j*np.pi*num_translations*k/L))

            elif op_string == 'yz':
                if isinstance(state_rep_j, int):
                    state_rep_j = bin(state_rep_j)[2:].zfill(L)
                    
                for (coupling_strength, site_index_1, site_index_2) \
                    in couplings:

                    z_value = (-1)**(int(state_rep_j[site_index_2]) + 1)

                    raised_state = raise_bits(state_rep_j,[site_index_1],L)
                    if raised_state != None:
                        flipped_state = raised_state
                        sigma_y_factor = -1.0j
                    elif raised_state == None:
                        flipped_state = lower_bits(state_rep_j,
                                                   [site_index_1], L)
                        sigma_y_factor = +1.0j

                    factor = z_value * sigma_y_factor
                                        
                    state_rep_i, num_translations = \
                           representative(flipped_state, L,
                                          translations_only=True)[:2]
                    i = find_in_sorted_list(state_rep_i,
                                              basis_reps_int_list)
                        # this is the flipped_state_rep index
                    R_i = basis_reps[i][1]
                    if i >= 0:
                        if k == 0 or abs(k) == int(L/2) == L/2:
                            op_matrix[i,j] += (coupling_strength * factor *
                                               np.sqrt(R_j/R_i) *
                        np.real(np.exp(2.0j*np.pi*num_translations*k/L)))
                        else:
                            op_matrix[i,j] += (coupling_strength * factor *
                                               np.sqrt(R_j/R_i) *
                                    np.exp(2.0j*np.pi*num_translations*k/L))

            elif op_string == 'zy':
                if isinstance(state_rep_j, int):
                    state_rep_j = bin(state_rep_j)[2:].zfill(L)
                    
                for (coupling_strength, site_index_1, site_index_2) \
                    in couplings:

                    z_value = (-1)**(int(state_rep_j[site_index_1]) + 1)

                    raised_state = raise_bits(state_rep_j,[site_index_2],L)
                    if raised_state != None:
                        flipped_state = raised_state
                        sigma_y_factor = -1.0j
                    elif raised_state == None:
                        flipped_state = lower_bits(state_rep_j,
                                                   [site_index_2], L)
                        sigma_y_factor = +1.0j

                    factor = z_value * sigma_y_factor
                                        
                    state_rep_i, num_translations = \
                           representative(flipped_state, L,
                                          translations_only=True)[:2]
                    i = find_in_sorted_list(state_rep_i,
                                              basis_reps_int_list)
                        # this is the flipped_state_rep index
                    R_i = basis_reps[i][1]
                    if i >= 0:
                        if k == 0 or abs(k) == int(L/2) == L/2:
                            op_matrix[i,j] += (coupling_strength * factor *
                                               np.sqrt(R_j/R_i) *
                        np.real(np.exp(2.0j*np.pi*num_translations*k/L)))
                        else:
                            op_matrix[i,j] += (coupling_strength * factor *
                                               np.sqrt(R_j/R_i) *
                                    np.exp(2.0j*np.pi*num_translations*k/L))

            elif op_string == 'xy':
                for (coupling_strength, site_index_1, site_index_2) in \
                    couplings:
                    
                    flipped_state = flip_bits(state_rep_j,[site_index_1],L)

                    raised_site_2 = raise_bits(flipped_state,
                                              [site_index_2], L)
                    if raised_site_2 != None:
                        flipped_state = raised_site_2
                        factor_site_2 = -1.0j
                    elif raised_site_2 == None:
                        flipped_state = lower_bits(flipped_state,
                                                   [site_index_2], L)
                        factor_site_2 = +1.0j

                    factor = factor_site_2

                    state_rep_i, num_translations = \
                               representative(flipped_state, L,
                                              translations_only=True)[:2]
                    i = find_in_sorted_list(state_rep_i,
                                        basis_reps_int_list)
                            # this is the flipped_state_rep index
                    R_i = basis_reps[i][1]
                    if i >= 0:
                        if k == 0 or abs(k) == int(L/2) == L/2:
                            op_matrix[i,j] += (factor *
                                    coupling_strength * np.sqrt(R_j/R_i)*
                        np.real(np.exp(2.0j*np.pi*num_translations*k/L)))
                        else:
                            op_matrix[i,j] += (factor *
                                    coupling_strength * np.sqrt(R_j/R_i)*
                            np.exp(2.0j*np.pi*num_translations*k/L))

            elif op_string == 'yx':
                for (coupling_strength, site_index_1, site_index_2) in \
                    couplings:
                    
                    flipped_state = flip_bits(state_rep_j,[site_index_2],L)

                    raised_site_1 = raise_bits(flipped_state,
                                              [site_index_1], L)
                    if raised_site_1 != None:
                        flipped_state = raised_site_1
                        factor_site_1 = -1.0j
                    elif raised_site_1 == None:
                        flipped_state = lower_bits(flipped_state,
                                                   [site_index_1], L)
                        factor_site_1 = +1.0j

                    factor = factor_site_1

                    state_rep_i, num_translations = \
                               representative(flipped_state, L,
                                              translations_only=True)[:2]
                    i = find_in_sorted_list(state_rep_i,
                                        basis_reps_int_list)
                            # this is the flipped_state_rep index
                    R_i = basis_reps[i][1]
                    if i >= 0:
                        if k == 0 or abs(k) == int(L/2) == L/2:
                            op_matrix[i,j] += (factor *
                                    coupling_strength * np.sqrt(R_j/R_i)*
                        np.real(np.exp(2.0j*np.pi*num_translations*k/L)))
                        else:
                            op_matrix[i,j] += (factor *
                                    coupling_strength * np.sqrt(R_j/R_i)*
                            np.exp(2.0j*np.pi*num_translations*k/L))

            elif op_string == '0x0':
                # `0' is `down', not `up' here
                if isinstance(state_rep_j, int):
                    state_rep_j = bin(state_rep_j)[2:].zfill(L)
                for (coupling_strength, site_index_1, site_index_2,
                     site_index_3) in couplings:

                    if (state_rep_j[site_index_1] == '0' and
                        state_rep_j[site_index_3] == '0'):

                        flipped_state = flip_bits(state_rep_j,
                                                  [site_index_2], L)
                        state_rep_i, num_translations = \
                               representative(flipped_state, L,
                                              translations_only=True)[:2]
                        i = find_in_sorted_list(state_rep_i,
                                                  basis_reps_int_list)
                            # this is the flipped_state_rep index
                        R_i = basis_reps[i][1]
                        if i >= 0:
                            if k == 0 or abs(k) == int(L/2) == L/2:
                                op_matrix[i,j] += (coupling_strength *
                                                   np.sqrt(R_j/R_i) *
                                        np.real(np.exp(2.0j*np.pi*
                                           num_translations*k/L)))
                            else:
                                op_matrix[i,j] += (coupling_strength *
                                                   np.sqrt(R_j/R_i) *
                                        np.exp(2.0j*np.pi*
                                               num_translations*k/L))

                    else:
                        
                        None
                
            elif op_string == '0x10':
                # `0' is `down', and `1' is `up' here
                if isinstance(state_rep_j, int):
                    state_rep_j = bin(state_rep_j)[2:].zfill(L)
                for (coupling_strength, site_index_1, site_index_2,
                     site_index_3, site_index_4) in couplings:

                    if (state_rep_j[site_index_1] == '0' and
                        state_rep_j[site_index_3] == '1' and
                        state_rep_j[site_index_4] == '0'):

                        flipped_state = flip_bits(state_rep_j,
                                                  [site_index_2], L)
                        state_rep_i, num_translations = \
                               representative(flipped_state, L,
                                              translations_only=True)[:2]
                        i = find_in_sorted_list(state_rep_i,
                                                  basis_reps_int_list)
                            # this is the flipped_state_rep index
                        R_i = basis_reps[i][1]
                        if i >= 0:
                            if k == 0 or abs(k) == int(L/2) == L/2:
                                op_matrix[i,j] += (coupling_strength *
                                                   np.sqrt(R_j/R_i) *
                                        np.real(np.exp(2.0j*np.pi*
                                           num_translations*k/L)))
                            else:
                                op_matrix[i,j] += (coupling_strength *
                                                   np.sqrt(R_j/R_i) *
                                        np.exp(2.0j*np.pi*
                                               num_translations*k/L))

                    else:
                        
                        None
                        
            elif op_string == '01x0':
                # `0' is `down', and `1' is `up' here
                if isinstance(state_rep_j, int):
                    state_rep_j = bin(state_rep_j)[2:].zfill(L)
                for (coupling_strength, site_index_1, site_index_2,
                     site_index_3, site_index_4) in couplings:

                    if (state_rep_j[site_index_1] == '0' and
                        state_rep_j[site_index_2] == '1' and
                        state_rep_j[site_index_4] == '0'):

                        flipped_state = flip_bits(state_rep_j,
                                                  [site_index_3], L)
                        state_rep_i, num_translations = \
                               representative(flipped_state, L,
                                              translations_only=True)[:2]
                        i = find_in_sorted_list(state_rep_i,
                                                  basis_reps_int_list)
                            # this is the flipped_state_rep index
                        R_i = basis_reps[i][1]
                        if i >= 0:
                            if k == 0 or abs(k) == int(L/2) == L/2:
                                op_matrix[i,j] += (coupling_strength *
                                                   np.sqrt(R_j/R_i) *
                                        np.real(np.exp(2.0j*np.pi*
                                           num_translations*k/L)))
                            else:
                                op_matrix[i,j] += (coupling_strength *
                                                   np.sqrt(R_j/R_i) *
                                        np.exp(2.0j*np.pi*
                                               num_translations*k/L))

                    else:
                        None
                
            elif op_string == '0x110':
                # `0' is `down', and `1' is `up' here
                if isinstance(state_rep_j, int):
                    state_rep_j = bin(state_rep_j)[2:].zfill(L)
                for (coupling_strength, site_index_1, site_index_2,
                     site_index_3, site_index_4, site_index_5) in couplings:

                    if (state_rep_j[site_index_1] == '0' and
                        state_rep_j[site_index_3] == '1' and
                        state_rep_j[site_index_4] == '1' and
                        state_rep_j[site_index_5] == '0'):

                        flipped_state = flip_bits(state_rep_j,
                                                  [site_index_2], L)
                        state_rep_i, num_translations = \
                               representative(flipped_state, L,
                                              translations_only=True)[:2]
                        i = find_in_sorted_list(state_rep_i,
                                                  basis_reps_int_list)
                            # this is the flipped_state_rep index
                        R_i = basis_reps[i][1]
                        if i >= 0:
                            if k == 0 or abs(k) == int(L/2) == L/2:
                                op_matrix[i,j] += (coupling_strength *
                                                   np.sqrt(R_j/R_i) *
                                        np.real(np.exp(2.0j*np.pi*
                                           num_translations*k/L)))
                            else:
                                op_matrix[i,j] += (coupling_strength *
                                                   np.sqrt(R_j/R_i) *
                                        np.exp(2.0j*np.pi*
                                               num_translations*k/L))

                    else:
                        None
                        
            elif op_string == '01x10':
                # `0' is `down', and `1' is `up' here
                if isinstance(state_rep_j, int):
                    state_rep_j = bin(state_rep_j)[2:].zfill(L)
                for (coupling_strength, site_index_1, site_index_2,
                     site_index_3, site_index_4, site_index_5) in couplings:

                    if (state_rep_j[site_index_1] == '0' and
                        state_rep_j[site_index_2] == '1' and
                        state_rep_j[site_index_4] == '1' and
                        state_rep_j[site_index_5] == '0'):

                        flipped_state = flip_bits(state_rep_j,
                                                  [site_index_3], L)
                        state_rep_i, num_translations = \
                               representative(flipped_state, L,
                                              translations_only=True)[:2]
                        i = find_in_sorted_list(state_rep_i,
                                                  basis_reps_int_list)
                            # this is the flipped_state_rep index
                        R_i = basis_reps[i][1]
                        if i >= 0:
                            if k == 0 or abs(k) == int(L/2) == L/2:
                                op_matrix[i,j] += (coupling_strength *
                                                   np.sqrt(R_j/R_i) *
                                        np.real(np.exp(2.0j*np.pi*
                                           num_translations*k/L)))
                            else:
                                op_matrix[i,j] += (coupling_strength *
                                                   np.sqrt(R_j/R_i) *
                                        np.exp(2.0j*np.pi*
                                               num_translations*k/L))

                    else:
                        None
                        
            elif op_string == '011x0':
                # `0' is `down', and `1' is `up' here
                if isinstance(state_rep_j, int):
                    state_rep_j = bin(state_rep_j)[2:].zfill(L)
                for (coupling_strength, site_index_1, site_index_2,
                     site_index_3, site_index_4, site_index_5) in couplings:

                    if (state_rep_j[site_index_1] == '0' and
                        state_rep_j[site_index_2] == '1' and
                        state_rep_j[site_index_3] == '1' and
                        state_rep_j[site_index_5] == '0'):

                        flipped_state = flip_bits(state_rep_j,
                                                  [site_index_4], L)
                        state_rep_i, num_translations = \
                               representative(flipped_state, L,
                                              translations_only=True)[:2]
                        i = find_in_sorted_list(state_rep_i,
                                                  basis_reps_int_list)
                            # this is the flipped_state_rep index
                        R_i = basis_reps[i][1]
                        if i >= 0:
                            if k == 0 or abs(k) == int(L/2) == L/2:
                                op_matrix[i,j] += (coupling_strength *
                                                   np.sqrt(R_j/R_i) *
                                        np.real(np.exp(2.0j*np.pi*
                                           num_translations*k/L)))
                            else:
                                op_matrix[i,j] += (coupling_strength *
                                                   np.sqrt(R_j/R_i) *
                                        np.exp(2.0j*np.pi*
                                               num_translations*k/L))

                    else:
                        None
                
            # elif op_string == '0x1110':
            #     # `0' is `down', and `1' is `up' here
            #     None
            # elif op_string == '01x110':
            #     # `0' is `down', and `1' is `up' here
            #     None
            # elif op_string == '011x10':
            #     # `0' is `down', and `1' is `up' here
            #     None
            # elif op_string == '0111x0':
            #     # `0' is `down', and `1' is `up' here
            #     None

            else:
                raise Exception("Operator string " + op_string +
                                " not yet implemented.")
                    

    return op_matrix

def psi_momentum_basis_to_computational_basis(psi, momentum_basis_reps,
                                              new_basis, k, L):
    """
    Given an input state psi in the k-block momentum basis return
    the same state in the new computational basis given by `new_basis'.

    The input state psi is in the k-block momentum basis, i.e.,

        |psi> = \sum_{j} psi_j |j(k)>

    where 

        |j(k)> = \sum_{r=0}^{L-1} exp(-2*pi*k*r/L) |j> / sqrt(N_j)

    and |j> is the representative of the state |j(k)> (see Sandvik2010 
    section 4.1.3 for details). The list of (representative, periodicity) 
    pairs are given in `momentum_basis_reps'.

    `new_basis' is a sorted list of integers, representing the 
    computational basis states of the new basis.

    The output is the same as the input state |psi>, but in the new_basis. 
    """

    dtype = psi.dtype
    dim_new = len(new_basis)
    psi_new_basis = np.zeros((1, dim_new), dtype=dtype)
    
    if len(psi) != len(momentum_basis_reps):
        raise AttributeError("Input vector not the expected length.")

    if dim_new < len(psi):
        raise AttributeError("New basis dimension should not be less " +
                             "than the old basis dimension.")

    if isinstance(new_basis[0], str):
        """If `new_basis' is a list of bit strings, convert to 
        corresponding integers."""
        new_basis = [int(state, 2) for state in new_basis]
    
    for i in range(len(psi)):
        rep_i, R_i = momentum_basis_reps[i]
        rep_i = int(rep_i, 2)
        N_i = L**2 / R_i

        if (k % (L/R_i)) != 0:
            raise ValueError("Momentum k is not consistent with the " +
                             "periodicity R of the representative.")
        
        for j in range(L):
            idx = find_in_sorted_list(rep_i, new_basis)
            if k == 0 or abs(k) == int(L/2) == L/2:
                if idx == -1:
                    continue
                elif idx > -1:
                    psi_new_basis[0,idx] += (psi[i] *
                        np.real(np.exp(-2.0j*np.pi*k*j/L)) / np.sqrt(N_i))
            else:
                if idx == -1:
                    continue
                elif idx > -1:
                    psi_new_basis[0,idx] += (psi[i] *
                                             np.exp(-2.0j*np.pi*k*j/L) /
                                             np.sqrt(N_i))
            rep_i = translate_right(rep_i, L)

    return psi_new_basis

######################################################################
# Construct semimomentum block basis
######################################################################
            
def checkstate_semimomentum(state, L, k):
    """
    This function takes a bitstring state as input and checks whether it
    should be included in the list of representatives of the semimomentum 
    basis. The state is only included if it is consistent with momentum
    k and reflection quantum number p.
    """
    
    if isinstance(state, str):
        "If state is a bit string, convert to corresponding integer."
        state = int(state, 2)

    if k > int(L/2) or k < 0:
        raise AttributeError("k is out of range for a semi-momentum state")

    translated_state = state
    for i in range(L):
        translated_state = translate_right(translated_state, L)
        if translated_state < state:
            R = -1
            break
        elif translated_state == state:
            if (k % (L/(i+1))) != 0:
                R = -1
                break
            else:
                R = i + 1
                break

    translated_reflected_state = reflect(state, L)
    m = -1
    for i in range(R):
        if translated_reflected_state < state:
            R = -1
            break
        elif translated_reflected_state == state:
            m = i
            break
        translated_reflected_state = \
                        translate_right(translated_reflected_state, L)

    return R, m

def semimomentum_basis_reps(basis, L, k, p):

    reps = []

    for state in basis:
        
        R, m = checkstate_semimomentum(state, L, k)

        if k == 0 or k == int(L/2) == L/2:
            sigma_list = [1]
        else:
            sigma_list = [1, -1]
            
        for sigma in sigma_list:
            R_sigma = R
            if m != -1:
                if 1 + sigma * p * np.cos(2.0 * np.pi * k * m / L) == 0:
                    R_sigma = -1
                if sigma == -1 and 1 - sigma*p*np.cos(2.0*np.pi*k*m/L) != 0:
                    R_sigma = -1
            if R_sigma > 0:
                reps.append((state, sigma * R, m))

    return reps

def semimomentum_op_element(basis_rep_i, basis_rep_j, l_i, q_i, k, p, L):
    """
    Gives the matrix element O_{ij} for an operator O in the semimomentum
    basis.
    """

    state_i, R_i, m_i = basis_rep_i
    sigma_i = np.sign(R_i)
    R_i = abs(R_i)

    state_j, R_j, m_j = basis_rep_j
    sigma_j = np.sign(R_j)
    R_j = abs(R_j)

    if k > int(L/2) or k < 0:
        raise AttributeError("k is out of range for a semi-momentum state")

    if k == 0 or k == int(L/2) == L/2:
        g_k = 2
    else:
        g_k = 1

    if m_i == -1:
        N_i = L**2 * g_k / R_i
    elif m_i >= 0:
        N_i = (L**2 * g_k / R_i) * (1 + sigma_i * p *
                                    np.cos(2 * np.pi * k * m_i / L))

    if m_j == -1:
        N_j = L**2 * g_k / R_j
    elif m_j >= 0:
        N_j = (L**2 * g_k / R_j) * (1 + sigma_j * p *
                                    np.cos(2 * np.pi * k * m_j / L))
    
    if sigma_j == sigma_i:
        if m_i == -1:
            return (sigma_j * p)**q_i * np.sqrt(N_i/N_j) * \
                np.cos(2 * np.pi * k * l_i / L)
        elif m_i >= 0:
            return (sigma_j * p)**q_i * np.sqrt(N_i/N_j) * \
                (np.cos(2 * np.pi * k * l_i / L) + sigma_j * p *
                 np.cos(2 * np.pi * k * (l_i - m_i) / L)) / \
                (1 + sigma_j * p * np.cos(2 * np.pi * k * m_i / L))

    elif sigma_j == - sigma_i:
        if m_i == -1:
            return (sigma_j * p)**q_i * np.sqrt(N_i/N_j) * \
                (-sigma_j * np.sin(2 * np.pi * k * l_i / L))
        elif m_i >= 0:
            return (sigma_j * p)**q_i * np.sqrt(N_i/N_j) * \
                (-sigma_j * np.sin(2 * np.pi * k * l_i / L) +
                 p * np.sin(2 * np.pi * k * (l_i - m_i) / L)) / \
                (1 - sigma_j * p * np.cos(2 * np.pi * k * m_i / L))
        
def op_semimomentum_block(L, k, p, basis_reps, op_descriptor):
    """
    Returns the matrix for an operator (specified by `op_descriptor') in 
    the (k,p)-block, and in the semimomentum basis specified by 
    `basis_reps'.

    *** The operator must be translationally invariant and reflection
    invariant, i.e., it must commute with the translation and parity 
    operators. ***

    Input
    -----
    L : int
        The number of spin-half particles.
    k : int, between -L/2+1 and L/2 (L even) or between -int(L/2) and
        int(L/2) (L odd).
        The momentum block. The integer k really represents the momentum
        2*pi*k/L.
    p : int, either +1 or -1.
        The parity block.
    basis_reps : list or array
        The list of integer representatives of the basis for the block.
    op_descriptor : list
        The list that specifies the operator. Each element of the
        list is itself a list of the form [op_string, couplings], where
        `op_string' is a string representing an operator, and `couplings'
        specifies the sites on which the operator acts, as well as the
        coupling constant.

        For example, for the operator O=\sum_{i=0}^{L-1} w \sigma_i^z
        we have op_descriptor = ["z", [[w, i] for i in range(L)]].

        See [SciPost Phys. 2, 003 (2017)] section 2.1 for more details.
    """
    
    dim = len(basis_reps)
    basis_reps_int_list = [int(state,2) for state in
                           np.array(basis_reps)[:,0]]
    #H_dim = len(set(basis_reps_int_list))

    if k > int(L/2) or k < 0:
        raise AttributeError("k is out of range for a semi-momentum state")

    op_matrix = sp.lil_matrix((dim, dim), dtype=np.float64)

    for j in range(dim):
        
        if j > 0 and basis_reps[j][0] == basis_reps[j-1][0]:
            continue
        elif j < dim - 1 and basis_reps[j][0] == basis_reps[j+1][0]:
            n = 2
        else:
            n = 1

        for op_string, couplings in op_descriptor:
            
            if op_string == 'x':
                for coupling_strength, site_index in couplings:
                    flipped_state = flip_bits(basis_reps[j][0],
                                              [site_index], L)
                    state_rep_i, l_i, q_i = representative(flipped_state, L,
                                          translations_only=False)
                    i = find_in_sorted_list(state_rep_i,
                                              basis_reps_int_list)
                                # this is flipped_state_rep index
                    if i >= 0:
                        if (i > 0 and
                            state_rep_i == int(basis_reps[i-1][0],2)):
                            m = 2
                            i = i - 1
                        elif (i < dim - 1 and
                              state_rep_i == int(basis_reps[i+1][0],2)):
                            m = 2
                        else:
                            m = 1

                        for i_ in range(i, i + m):
                            for j_ in range(j, j + n):
                                h = coupling_strength
                                op_matrix[i_,j_]+=h*semimomentum_op_element(
                                    basis_reps[i_], basis_reps[j_],
                                    l_i, q_i, k, p, L)
                                
            elif op_string == 'y':
                op_matrix = op_matrix.astype(complex)
                print('\n', 'WARNING: the conversion to a complex matrix',
                      ' here seems to be inefficient. Better to put it',
                      ' outside the loop', '\n')
                for coupling_strength, site_index in couplings:
                    raised_state = raise_bits(basis_reps[j][0],
                                              [site_index],L)
                    if raised_state != None:
                        flipped_state = raised_state
                        sigma_y_factor = -1.0j
                    elif raised_state == None:
                        flipped_state = lower_bits(basis_reps[j][0],
                                                   [site_index], L)
                        sigma_y_factor = +1.0j
                                            
                    state_rep_i, l_i, q_i = representative(flipped_state, L,
                                          translations_only=False)
                    i = find_in_sorted_list(state_rep_i,
                                              basis_reps_int_list)
                                # this is flipped_state_rep index
                    if i >= 0:
                        if (i > 0 and
                            state_rep_i == int(basis_reps[i-1][0],2)):
                            m = 2
                            i = i - 1
                        elif (i < dim - 1 and
                              state_rep_i == int(basis_reps[i+1][0],2)):
                            m = 2
                        else:
                            m = 1

                        for i_ in range(i, i + m):
                            for j_ in range(j, j + n):
                                h = sigma_y_factor * coupling_strength
                                op_matrix[i_,j_]+=h*semimomentum_op_element(
                                    basis_reps[i_], basis_reps[j_],
                                    l_i, q_i, k, p, L)
            elif op_string == 'z':
                coupling_strength = couplings[0][0]
                for j_ in range(j, j + n):
                    op_matrix[j_,j_] += 2.0 * coupling_strength * \
                            checkstate_magnetization(basis_reps[j_][0],L)

            elif op_string == 'xx':
                for (coupling_strength, site_index_1, site_index_2) in \
                    couplings:
                    flipped_state = flip_bits(basis_reps[j][0],
                                            [site_index_1,site_index_2], L)
                    state_rep_i, l_i, q_i = representative(flipped_state, L,
                                          translations_only=False)
                    i = find_in_sorted_list(state_rep_i,
                                              basis_reps_int_list)
                                # this is flipped_state_rep index
                    if i >= 0:
                        if (i > 0 and
                            state_rep_i == int(basis_reps[i-1][0],2)):
                            m = 2
                            i = i - 1
                        elif (i < dim - 1 and
                              state_rep_i == int(basis_reps[i+1][0],2)):
                            m = 2
                        else:
                            m = 1

                        for i_ in range(i, i + m):
                            for j_ in range(j, j + n):
                                h = coupling_strength
                                op_matrix[i_,j_]+=h*semimomentum_op_element(
                                    basis_reps[i_], basis_reps[j_],
                                    l_i, q_i, k, p, L)

            elif op_string == 'yy':
                for (coupling_strength, site_index_1, site_index_2) in \
                    couplings:
                    
                    raised_site_1 = raise_bits(basis_reps[j][0],
                                              [site_index_1],L)
                    if raised_site_1 != None:
                        flipped_state = raised_site_1
                        factor_site_1 = -1.0j
                    elif raised_site_1 == None:
                        flipped_state = lower_bits(basis_reps[j][0],
                                                   [site_index_1], L)
                        factor_site_1 = +1.0j

                    raised_site_2 = raise_bits(flipped_state,
                                              [site_index_2], L)
                    if raised_site_2 != None:
                        flipped_state = raised_site_2
                        factor_site_2 = -1.0j
                    elif raised_site_2 == None:
                        flipped_state = lower_bits(flipped_state,
                                                   [site_index_2], L)
                        factor_site_2 = +1.0j

                    factor = np.real(factor_site_1 * factor_site_2)
                                            
                    state_rep_i, l_i, q_i = representative(flipped_state, L,
                                          translations_only=False)
                    i = find_in_sorted_list(state_rep_i,
                                              basis_reps_int_list)
                                # this is flipped_state_rep index
                    if i >= 0:
                        if (i > 0 and
                            state_rep_i == int(basis_reps[i-1][0],2)):
                            m = 2
                            i = i - 1
                        elif (i < dim - 1 and
                              state_rep_i == int(basis_reps[i+1][0],2)):
                            m = 2
                        else:
                            m = 1

                        for i_ in range(i, i + m):
                            for j_ in range(j, j + n):
                                h = factor * coupling_strength
                                op_matrix[i_,j_]+=h*semimomentum_op_element(
                                    basis_reps[i_], basis_reps[j_],
                                    l_i, q_i, k, p, L)

            elif op_string == 'zz':
                for (coupling_strength, site_index_1,
                    site_index_2) in couplings:
                    for j_ in range(j, j + n):
                        sz_1 = -(-1)**int(basis_reps[j_][0][site_index_1%L])
                        sz_2 = -(-1)**int(basis_reps[j_][0][site_index_2%L])
                        zz_value = sz_1 * sz_2
                        op_matrix[j_,j_] += coupling_strength * zz_value

            elif op_string == 'xz':
                for (coupling_strength, site_index_1, site_index_2) \
                    in couplings:
                    
                    flipped_state = flip_bits(basis_reps[j][0],
                                              [site_index_1],L)
                    state_rep_i, l_i, q_i = representative(flipped_state, L,
                                          translations_only=False)
                    i = find_in_sorted_list(state_rep_i,
                                              basis_reps_int_list)
                                # this is flipped_state_rep index
                    if i >= 0:
                        if (i > 0 and
                            state_rep_i == int(basis_reps[i-1][0],2)):
                            m = 2
                            i = i - 1
                        elif (i < dim - 1 and
                              state_rep_i == int(basis_reps[i+1][0],2)):
                            m = 2
                        else:
                            m = 1

                        for i_ in range(i, i + m):
                            for j_ in range(j, j + n):
                                z_value = (-1)** \
                                 (int(basis_reps[j_][0][site_index_2%L])+1)
                                h = coupling_strength * z_value
                                op_matrix[i_,j_]+=h*semimomentum_op_element(
                                    basis_reps[i_], basis_reps[j_],
                                    l_i, q_i, k, p, L)

            elif op_string == 'zx':
                for (coupling_strength, site_index_1, site_index_2) \
                    in couplings:
                    
                    flipped_state = flip_bits(basis_reps[j][0],
                                              [site_index_2],L)
                    state_rep_i, l_i, q_i = representative(flipped_state, L,
                                          translations_only=False)
                    i = find_in_sorted_list(state_rep_i,
                                              basis_reps_int_list)
                                # this is flipped_state_rep index
                    if i >= 0:
                        if (i > 0 and
                            state_rep_i == int(basis_reps[i-1][0],2)):
                            m = 2
                            i = i - 1
                        elif (i < dim - 1 and
                              state_rep_i == int(basis_reps[i+1][0],2)):
                            m = 2
                        else:
                            m = 1

                        for i_ in range(i, i + m):
                            for j_ in range(j, j + n):
                                z_value = (-1)** \
                                 (int(basis_reps[j_][0][site_index_1%L])+1)
                                h = coupling_strength * z_value
                                op_matrix[i_,j_]+=h*semimomentum_op_element(
                                    basis_reps[i_], basis_reps[j_],
                                    l_i, q_i, k, p, L)

            elif op_string == 'xy':
                op_matrix = op_matrix.astype(complex)
                for (coupling_strength, site_index_1, site_index_2) in \
                    couplings:
                    
                    flipped_state = flip_bits(basis_reps[j][0],
                                              [site_index_1],L)

                    raised_site_2 = raise_bits(flipped_state,
                                              [site_index_2], L)
                    if raised_site_2 != None:
                        flipped_state = raised_site_2
                        factor_site_2 = -1.0j
                    elif raised_site_2 == None:
                        flipped_state = lower_bits(flipped_state,
                                                   [site_index_2], L)
                        factor_site_2 = +1.0j

                    factor = factor_site_2

                    state_rep_i, l_i, q_i = representative(flipped_state, L,
                                          translations_only=False)
                    i = find_in_sorted_list(state_rep_i,
                                        basis_reps_int_list)
                            # this is the flipped_state_rep index

                    if i >= 0:
                        if (i > 0 and
                            state_rep_i == int(basis_reps[i-1][0],2)):
                            m = 2
                            i = i - 1
                        elif (i < dim - 1 and
                              state_rep_i == int(basis_reps[i+1][0],2)):
                            m = 2
                        else:
                            m = 1

                        for i_ in range(i, i + m):
                            for j_ in range(j, j + n):
                                h = factor * coupling_strength
                                op_matrix[i_,j_]+=h*semimomentum_op_element(
                                    basis_reps[i_], basis_reps[j_],
                                    l_i, q_i, k, p, L)

            elif op_string == 'yx':
                op_matrix = op_matrix.astype(complex)
                for (coupling_strength, site_index_1, site_index_2) in \
                    couplings:
                    
                    flipped_state = flip_bits(basis_reps[j][0],
                                              [site_index_2],L)

                    raised_site_1 = raise_bits(flipped_state,
                                              [site_index_1], L)
                    if raised_site_1 != None:
                        flipped_state = raised_site_1
                        factor_site_1 = -1.0j
                    elif raised_site_1 == None:
                        flipped_state = lower_bits(flipped_state,
                                                   [site_index_1], L)
                        factor_site_1 = +1.0j

                    factor = factor_site_1

                    state_rep_i, l_i, q_i = representative(flipped_state, L,
                                          translations_only=False)
                    
                    i = find_in_sorted_list(state_rep_i,
                                        basis_reps_int_list)
                            # this is the flipped_state_rep index

                    if i >= 0:
                        if (i > 0 and
                            state_rep_i == int(basis_reps[i-1][0],2)):
                            m = 2
                            i = i - 1
                        elif (i < dim - 1 and
                              state_rep_i == int(basis_reps[i+1][0],2)):
                            m = 2
                        else:
                            m = 1

                        for i_ in range(i, i + m):
                            for j_ in range(j, j + n):
                                h = factor * coupling_strength
                                op_matrix[i_,j_]+=h*semimomentum_op_element(
                                    basis_reps[i_], basis_reps[j_],
                                    l_i, q_i, k, p, L)

            elif op_string == 'zzz':
                for (coupling_strength, site_index_1,
                     site_index_2, site_index_3) in couplings:
                    for j_ in range(j, j + n):
                        sz_1 = -(-1)**int(basis_reps[j_][0][site_index_1%L])
                        sz_2 = -(-1)**int(basis_reps[j_][0][site_index_2%L])
                        #sz_3 = -(-1)**int(basis_reps[j_][0]
                        #                  [(site_index_2+1)%L])
                        sz_3 = -(-1)**int(basis_reps[j_][0][site_index_3%L])
                        zzz_value = sz_1 * sz_2 * sz_3
                        op_matrix[j_,j_] += coupling_strength * zzz_value

            elif op_string == '0x0':
                # `0' is `down', not `up' here
                None
                
            elif op_string == '0x10':
                # `0' is `down', and `1' is `up' here
                None
            elif op_string == '01x0':
                # `0' is `down', and `1' is `up' here
                None
                
            elif op_string == '0x110':
                # `0' is `down', and `1' is `up' here
                None
            elif op_string == '01x10':
                # `0' is `down', and `1' is `up' here
                None
            elif op_string == '011x0':
                # `0' is `down', and `1' is `up' here
                None
                
            elif op_string == '0x1110':
                # `0' is `down', and `1' is `up' here
                None
            elif op_string == '01x110':
                # `0' is `down', and `1' is `up' here
                None
            elif op_string == '011x10':
                # `0' is `down', and `1' is `up' here
                None
            elif op_string == '0111x0':
                # `0' is `down', and `1' is `up' here
                None

            else:
                raise Exception("Operator string " + op_string +
                                " not yet implemented.")
    
    return op_matrix

def psi_semimomentum_basis_to_computational_basis(psi,
                        semimomentum_basis_reps, new_basis, k, p, L):
    """
    Given an input state psi in the (k,p) semimomentum block basis, return
    the same state in the new computational basis given by `new_basis'.

    The input state psi is in the semimomentum basis, i.e.,

        |psi> = \sum_{j} psi_j |j^{sigma}(k,p)>

    where 

        |j^{sigma}(k,p)> = \sum_{r=0}^{L-1} C_k^{sigma}(r) (1+pP) * 
                           T^r |j> / sqrt(N^sigma_j)

    and |j> is the representative of the state |j(k,p)> (see Sandvik2010 
    section 4.1.4 for details, esp. Eq. 142). The list of (representative, 
    sigma * periodicity, m) triples are given in `semimomentum_basis_reps'.

    `new_basis' is a sorted list of integers, representing the 
    computational basis states of the new basis.

    The output is the same as the input state |psi>, but in the new_basis. 
    """

    dtype = psi.dtype
    dim_new = len(new_basis)
    psi_new_basis = np.zeros((1, dim_new), dtype=dtype)
    
    if len(psi) != len(semimomentum_basis_reps):
        raise AttributeError("Input vector not the expected length.")

    if dim_new < len(psi):
        raise AttributeError("New basis dimension should not be less " +
                             "than the old basis dimension.")

    if isinstance(new_basis[0], str):
        """If `new_basis' is a list of bit strings, convert to 
        corresponding integers."""
        new_basis = [int(state, 2) for state in new_basis]

    for i in range(len(psi)):
        rep_i, sigmaR_i, m_i = semimomentum_basis_reps[i]
        rep_i = int(rep_i, 2)
        sigma_i = np.sign(sigmaR_i)
        R_i = abs(sigmaR_i)

        P_rep_i = reflect(rep_i, L)

        if k == 0 or k == int(L/2) == L/2:
            g_k = 2
        else:
            g_k = 1

        if m_i == -1:
            N_i = L**2 * g_k / R_i
        elif m_i >= 0:
            N_i = (L**2 * g_k / R_i) * (1 + sigma_i * p * \
                                        np.cos(2 * np.pi * k * m_i / L))

        if (k % (L/R_i)) != 0:
            raise ValueError("Momentum k is not consistent with the " +
                             "periodicity R of the representative.")

        for j in range(L):
            
            idx_1 = find_in_sorted_list(rep_i, new_basis)
            idx_2 = find_in_sorted_list(P_rep_i, new_basis)

            if sigma_i == +1:
                C_k = np.cos(2.0*np.pi*k*j/L)
            elif sigma_i == -1:
                C_k = np.sin(2.0*np.pi*k*j/L)

            if idx_1 == -1 and idx_2 == -1:
                continue
            elif idx_1 > -1 and idx_2 > -1:
                psi_new_basis[0, idx_1] += psi[i] * C_k / np.sqrt(N_i)
                psi_new_basis[0, idx_2] += psi[i] * p * C_k / np.sqrt(N_i)
            else:
                raise AttributeError("Either idx_1 or idx_2 were not " +
                                     "found in new_basis.")
            
            rep_i = translate_right(rep_i, L)
            P_rep_i = reflect(rep_i, L)

    return psi_new_basis

#####################################################################
# Construct operator without symmetries (but possibly with constraints)
#####################################################################

def op_constructor(L, op_descriptor, basis):

    dim = len(basis)
    basis = [int(state,2) for state in np.array(basis)]

    real_couplings = True
    for op_string, couplings in op_descriptor:
        coupling_strength = couplings[0][0]
        if np.imag(coupling_strength) != 0:
            real_couplings = False

    if real_couplings:
        dtype = np.float64
    elif not real_couplings:
        dtype = complex

    op_matrix = sp.lil_matrix((dim, dim), dtype=dtype)

    for j in range(dim):

        state_j = basis[j]

        for op_string, couplings in op_descriptor:

            if op_string == 'x':
                for coupling_strength, site_index in couplings:
                    flipped_state = flip_bits(state_j, [site_index], L)
                    i = find_in_sorted_list(flipped_state, basis)
                    if i >= 0:
                        op_matrix[i,j] += coupling_strength

            elif op_string == 'z':
                for coupling_strength, site_index in couplings:
                    state_binary = bin(state_j)[2:].zfill(L)
                    op_matrix[j,j] += (2 * coupling_strength *
                                       (int(state_binary[site_index])-0.5))

            else:
                raise ValueError("op_string not yet implemented")
    
    return op_matrix

#####################################################################
# Construct Hamiltonian block matrix
#####################################################################

def hamiltonian_block(L, k, p, basis_reps, ham_descriptor):
    if len(basis_reps) == 0:
        raise AttributeError("This block is 0-dimensional")
    if p == None:
        return op_momentum_block(L, k, basis_reps, ham_descriptor)
    elif p != None:
        return op_semimomentum_block(L, k, p, basis_reps,
                                              ham_descriptor)

#####################################################################
# Functions to generate data
#####################################################################

def write_eigvec_exp_vals(eigen_data, obs_descriptor_list):

    ########################################
    # Unpack eigen_data
    ########################################

    #L, l, eigvals, eigvecs, block_basis_reps, k, p = eigen_data
    params, eigvals, eigvecs, block_basis_reps = eigen_data
    L = params['L']
    k = params['k']
    p = params['p']
    m = params['m']

    ########################################
    # Work out eigenstate expectation values
    ########################################

    obs_exp_vals_list = []
    for obs_descriptor in obs_descriptor_list:
        
        if p == None and k != None:
            obs = op_momentum_block(L, k, block_basis_reps, obs_descriptor)
            obs_exp_val_matrix = eigvecs.T.conj() @ obs @ eigvecs
            obs_exp_vals_list.append(np.diag(obs_exp_val_matrix))
            del obs, obs_exp_val_matrix
        elif p != None and k != None:
            obs = op_semimomentum_block(L, k, p, block_basis_reps,
                                        obs_descriptor)
            obs_exp_val_matrix = eigvecs.T.conj() @ obs @ eigvecs
            obs_exp_vals_list.append(np.diag(obs_exp_val_matrix))
            del obs, obs_exp_val_matrix
        elif p == None and k == None and m != None:
            basis = np.array(block_basis_reps)[:,0]
            obs = op_magnetization_block(L,m,basis,obs_descriptor)
            obs_exp_val_matrix = eigvecs.T.conj() @ obs @ eigvecs
            obs_exp_vals_list.append(np.diag(obs_exp_val_matrix))
            del obs, obs_exp_val_matrix
        
    ########################################
    # Work out canonical expectation values
    ########################################

    def Z_partition(beta, energy_eigvals):
        return sum([np.exp(-beta * E) for E in energy_eigvals])

    def E_canonical(beta, energy_eigvals, delta_beta=1e-6):
        Z_plus = Z_partition(beta + delta_beta, energy_eigvals)
        Z_minus = Z_partition(beta - delta_beta, energy_eigvals)
        return -(np.log(Z_plus) - np.log(Z_minus)) / (2*delta_beta)

    def O_canonical(beta, energy_eigvals, O_exp_vals):
        O_sum = sum([np.exp(-beta * energy_eigvals[i]) * O_exp_vals[i]
                     for i in range(len(energy_eigvals))])
        return O_sum / Z_partition(beta, energy_eigvals)

    beta_list = np.linspace(-10,10,400)
    E_canonical_list = [E_canonical(beta, eigvals) for beta in beta_list]

    obs_can_exp_vals_list = []
    for obs_exp_vals in obs_exp_vals_list:
        obs_can_exp_vals = [O_canonical(beta, eigvals, obs_exp_vals)
                            for beta in beta_list]
        obs_can_exp_vals_list.append(obs_can_exp_vals)

    ########################################

    exp_val_data = [params,
                    eigvals,
                    obs_exp_vals_list,
                    E_canonical_list,
                    obs_can_exp_vals_list]

    return exp_val_data

def scrape_ETH_indicators(E_window_centre_list, delta_E,
                          eigvals, exp_vals):
    """
    For a list of energies E_window_centre_list, this function returns the 
    microcanonical averages of some observable in a window around the 
    energies in the list, as well as the maximum deviations and standard 
    deviations from the microcanonical average in that window.
    """
    exp_vals_in_energy_window_list = [[] for E in E_window_centre_list]

    for i in range(len(eigvals)):
        eigval_ = eigvals[i]
        exp_val_ = exp_vals[i]
        for j in range(len(E_window_centre_list)):
            E = E_window_centre_list[j]
            if eigval_ >= E - delta_E and eigval_ <= E + delta_E:
                exp_vals_in_energy_window_list[j].append(exp_val_)
                #eigvals_in_energy_window_list[j].append(eigval_)

    exp_vals_mean_list = []
    I_S_list = []
    I_W_list = []
    for j in range(len(E_window_centre_list)):
        if len(exp_vals_in_energy_window_list[j]) == 0:
            exp_vals_mean_list.append(np.nan)
            I_S_list.append(np.nan)
            I_W_list.append(np.nan)
        else:
            exp_vals_mean_list.append(
                np.mean(exp_vals_in_energy_window_list[j]))
            I_S_list.append(
                max(abs(np.array(exp_vals_in_energy_window_list[j]) -
                        exp_vals_mean_list[j])))
            I_W_list.append(
                np.sqrt(sum((np.array(exp_vals_in_energy_window_list[j]) -
                             exp_vals_mean_list[j])**2) / \
                        len(exp_vals_in_energy_window_list[j])))
                
    return I_S_list, I_W_list, exp_vals_mean_list

#####################################################################
# Test functions
#####################################################################

def test_translate_left(L=3):
    for i in range(2**L):
        print(i, bin(i)[2:].zfill(L), ' '*4,
              bin(translate_left(i,L))[2:].zfill(L),
              translate_left(bin(i)[2:].zfill(L),L))

def test_translate_right(L=3):
    for i in range(2**L):
        print(i, bin(i)[2:].zfill(L), ' '*4,
              bin(translate_right(i,L))[2:].zfill(L),
              translate_right(bin(i)[2:].zfill(L),L))

def test_reflect(L=3):
    for i in range(2**L):
        print(i, bin(i)[2:].zfill(L), ' '*4,
              bin(reflect(i,L))[2:].zfill(L),
              reflect(bin(i)[2:].zfill(L),L))

        
