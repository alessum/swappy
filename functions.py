import numpy as np
import scipy.linalg as la
import datetime, timeit
import random as rd
import numpy.random as nprd
import scipy.special as scsp
import scipy.linalg as spla
import shutil
terminal_width, _ = shutil.get_terminal_size()
from functools import reduce


# import os
# # os.environ['NUMBA_THREADING_LAYER'] = 'workqueue'
from numba import njit, prange#, config, threading_layer

# # set the threading layer before any parallel target compilation
# config.THREADING_LAYER = 'threadsafe'

##########################################################################
# Timekeeping functions
##########################################################################

def begin(verbosity=1):
    if verbosity==2:
        print('\n')
        print('*' * terminal_width)
        print(' '*4, 'Started:', datetime.datetime.now())
    return None

def finish(verbosity=1):
    if verbosity==2:
        print(' '*4, 'Finished:', datetime.datetime.now())
        print('*' * terminal_width)
        print('\n')
    return None

def tic(task_description_string, verbosity=1):
    if verbosity==2:
        print('-' * terminal_width)
        print('---> ' + task_description_string)
    return timeit.default_timer()

def toc(tic_time, verbosity=1):
    toc_time = timeit.default_timer()
    if verbosity==2:
        print(' '*4, round(toc_time - tic_time, 6), 'seconds')
    return toc_time

#########################################################################

I = np.diag([1, 
               1])
X = np.array([[0,1],
              [1,0]])
Y = np.array([[0,-1j],
              [1j,0]])
Z = np.array([[1, 0],
              [0,-1]])
M = np.array([[0,1],
              [0,0]])
P = np.array([[0,0],
              [1,0]])

II = np.kron(I,I)
IX = np.kron(I,X)
XI = np.kron(X,I)
IZ = np.kron(I,Z)
ZI = np.kron(Z,I)
XX = np.kron(X,X)
YY = np.kron(Y,Y)
ZZ = np.kron(Z,Z)
PM = np.kron(P,M)
MP = np.kron(M,P)

#########################################################################

system_is_big_enough = False

def maybe_decorate(system_is_big_enough=system_is_big_enough):
    '''
    Apply the njit decorator to a function if the system size is big enough.
    '''
    if system_is_big_enough:
        return njit(parallel=False, fastmath=True, cache=True)
    else:
        return lambda x: x  # if condition is not met, return a no-op decorator
    
def maybe_decorate_no_parallel(system_is_big_enough=system_is_big_enough):
    '''
    Apply the njit decorator to a function if the system size is big enough.
    '''
    if system_is_big_enough:
        return njit()
    else:
        return lambda x: x  # if condition is not met, return a no-op decorator

@maybe_decorate(system_is_big_enough)
def u_01(psi, factors, qubits_01_same_mask,
         qubit_0_up_mask, qubits_01_flip_reindexing):

    psi_01_same = np.multiply(qubits_01_same_mask, psi)
    psi_01_differ = psi - psi_01_same

    psi_11 = np.multiply(qubit_0_up_mask, psi_01_same)
    psi_00 = (psi_01_same-psi_11)
    psi_00 *= factors[0,0]
    psi_11 *= factors[3,3]

    psi_01 = np.multiply(qubit_0_up_mask, psi_01_differ)
    psi_10 = psi_01_differ-psi_01
    psi_10 = factors[1,1] * psi_10 + factors[2,1] * psi_10[qubits_01_flip_reindexing]
    psi_01 = factors[2,2] * psi_01 + factors[1,2] * psi_01[qubits_01_flip_reindexing]

    psi_out = psi_00 + psi_01 + psi_10 + psi_11
    return psi_out

# @maybe_decorate(system_is_big_enough)
def U_floquet(psi, U_params, basis_data_for_U):
    '''
    Apply the Floquet operator to the state psi 2-qubit gate at a time
    '''
    gates_parameters, gate_ordering_idx_list = U_params
    translation_reindexing, qubits_01_same_mask, \
        qubit_0_up_mask, qubits_01_flip_reindexing = basis_data_for_U

    old_gate_idx = 0
    for order_idx, gate_idx in (enumerate(gate_ordering_idx_list)):
        psi = psi[translation_reindexing[gate_idx - old_gate_idx]]
        psi = u_01(psi, gates_parameters[order_idx], qubits_01_same_mask, 
                        qubit_0_up_mask, qubits_01_flip_reindexing)
        old_gate_idx = gate_idx
    return psi[translation_reindexing[-gate_ordering_idx_list[-1]]]

# @maybe_decorate(system_is_big_enough)
def g_evolution(psi, U_params, basis_data_for_U, phi_target, k):
    '''
    Apply the POLFED of the Floquet operator to the state psi k times
    '''
    psi_out = 0
    for i in range(k+1):
        if i == 0:
            psi_temp = psi.copy()
        elif i > 0:
            psi_temp = (np.exp(-1.0j * phi_target) *
                        U_floquet(psi, U_params, basis_data_for_U))
        psi_out = psi_out + psi_temp
    
    return psi_out

#########################################################################

def U_tilde(U):
    """
    The input should be a (d^2 x d^2)-dimensional unitary matrix, which
    acts on a bipartite Hilbert space $H \otimes H$ where d = dim(H).

    The output is the dual operator U_tilde, which is unitary if U is 
    dual-unitary.
    """

    d = int(np.sqrt(np.shape(U)[0]))

    U_reshape = np.reshape(U, (d,d,d,d))
        # turn the unitary matrix into a four-index tensor
    U_reshape_swap = np.swapaxes(U_reshape, 0, 3)
        # swap the first and last tensor indices
    U_reshape_swap_reshape = np.reshape(U_reshape_swap, (d**2, d**2))
        # convert the operator with shuffled indices back to a matrix

    return U_reshape_swap_reshape

def operator_schmidt_coeffs(U):

    """
    The input should be a (d^2 x d^2)-dimensional unitary matrix, which
    acts on a bipartite Hilbert space $H \otimes H$ where d = dim(H).

    The output are the Schmidt coefficients corresponding to the
    'operator entanglement' of U.
    """
    
    schmidt_coeffs = la.svd(U_tilde(U), compute_uv=False)

    return schmidt_coeffs

def XXZ_gate_operator_entanglement(J, Delta):
    """Entropy of the normalised operator Schmidt coefficients"""
    U_XX = II * np.cos(J) - 1.0j * XX * np.sin(J)
    U_YY = II * np.cos(J) - 1.0j * YY * np.sin(J)
    U_ZZ = II * np.cos(J*Delta) - 1.0j * ZZ * np.sin(J*Delta)
    U_XXZ = U_XX @ U_YY @ U_ZZ
    
    schmidt_coeffs = operator_schmidt_coeffs(U_XXZ)
    normalised_schmidt_coeffs = schmidt_coeffs**2 / 4 # now they sum to unity

    second_renyi_entropy = -np.log(sum((normalised_schmidt_coeffs)**2))
    shannon_entropy = sum([-s*np.log(s) for s in normalised_schmidt_coeffs])
    
    return shannon_entropy # second_renyi_entropy # 

def P(J_x, J_y, J_z):
    """See Hahn2023, Eq. 6. Note that J_x = 0.5*pi*c_1, etc."""
    return (14 + 4*np.cos(4*J_x) + 4*np.cos(4*J_y) + 4*np.cos(4*J_z) +
            np.cos(4*(J_x - J_y)) + np.cos(4*(J_x + J_y)) +
            np.cos(4*(J_x - J_z)) + np.cos(4*(J_x + J_z)) +
            np.cos(4*(J_y - J_z)) + np.cos(4*(J_y + J_z)) )

def s(J_x, J_y, J_z):
    return -np.log(P(J_x, J_y, J_z)/32)

#########################################################################

def gate_xxz_disordered(J, Jz, h1, h2, h3, h4):
    """Return the unitary matrix for the disordered XXZ model.
    J and Jz from 0 to pi/4"""
    U_H1 = np.diag(np.exp(-.5j*np.array([h1+h2, h1-h2, h2-h1, -h1-h2])))
    U_H2 = np.diag(np.exp(-.5j*np.array([h3+h4, h3-h4, h4-h3, -h3-h4])))
    U_XX = II * np.cos(J) - 1.0j * XX * np.sin(J)
    U_YY = II * np.cos(J) - 1.0j * YY * np.sin(J)
    U_ZZ = II * np.cos(Jz) - 1.0j * ZZ * np.sin(Jz)
    U_XXZ = U_XX @ U_YY @ U_ZZ
    return U_H1 @ U_XXZ @ U_H2

def gate_xxz_disordered(J, Jz, h1, h2, phi):
    ''' phase diagram [0,Pi] x [0,Pi]
    SWAP at J = pi
    '''
    U_H1 = np.diag(np.exp(-.5j*np.array([h1+h2, h1-h2, h2-h1, -h1-h2])))
    U_PM_MP = la.expm(-1j * J/2 * (PM * np.exp(1.0j * phi) + \
                                   MP * np.exp(-1.0j * phi)))
    U_ZZ = II * np.cos(Jz/4) - 1j * ZZ * np.sin(Jz/4) 
    U_XXZ = U_PM_MP @ U_ZZ
    return U_H1 @ U_XXZ


def gate_from_gue(a,b,c,d,e,f):
    """
    Given the parameters of a GUE matrix, return the unitary matrix
    obtained by exponentiating the GUE matrix.
    NOTE: The GUE matrix is of the form
              ┌                        ┐
              │  a    .       .     .  │
              │  .    b     e+im*f  .  │
        GUE = │  .  e-im*f    c     .  │
              │  .    .       .     d  │
              └                        ┘
    """
    h = np.diag([a, b, c, d]) + 0j
    h[1,2] = e+1j*f
    h[2,1] = e-1j*f
    return spla.expm(-1j*h)

def u3(theta, phi, lam):
    return np.array([
        [np.cos(theta/2), -np.exp(1j*lam)*np.sin(theta/2)],
        [np.exp(1j*phi)*np.sin(theta/2), np.exp(1j*lam+1j*phi)*np.cos(theta/2)]
    ], dtype=complex)

def gate_from_cue(phi1, phi2, phi3, theta, phi, lam):
    """
    Given the parameters of a GUE matrix, return the unitary matrix
    obtained by exponentiating the GUE matrix.
    NOTE: The GUE matrix is of the form
              ┌                                                             ┐
              │  e^(-im*phi1)                .                      .       │
        CUE = │       .       e^(-im*phi2)U3(theta, phi, lam)       .       │
              │       .                      .                e^(-im*phi3)  │
              └                                                             ┘
    """
    blocks = [np.exp(-1j*phi1), np.exp(-1j*phi2)*u3(theta/2, phi, lam), np.exp(-1j*phi3)]
    return spla.block_diag(*blocks)


def increment_gen():
    count = 0
    while True:
        yield count
        count += 1


def create_sZ_diag(r, N, block_basis):
    ''' 
    Create the s_r^z diag matrix
    '''
    paulis = [np.array([1,1], dtype=complex)] * N
    paulis[r] = np.array([1,-1])/np.sqrt(len(block_basis))
    return reduce(np.kron, paulis)[block_basis]


def print_matr(matr, precision=4):
    s = [[str(e) if abs(e) > 1e-15 else '.' for e in row] for row in np.round(matr,precision)]
    lens = [max(map(len, col)) for col in zip(*s)]
    fmt = '\t'.join('{{:{}}}'.format(x) for x in lens if x != 0) or '.'
    table = [fmt.format(*row) for row in s]
    print('\n'.join(table))



########
# New functions!!
########
import exact_diagonalization as ed

def get_filter(N, first_qubit, m=None):
    # TODO: sites being counted from R to L, inshallah
    first_qubit = (N - first_qubit - 2)%N
    if m is not None:
        basis = np.array(ed.magnetization_basis(range(2**N), N, m))
    else:
        basis = range(2**N)

    # Selects the basis states where the first qubit is up:
    # eg. for N=3, first_qubit=0, mask0_ = [0,1,2,3] == [000, 001, 010, 011]
    # their numbers will still correspond to the numbers in the comp basis
    filter0_ = basis[(basis >> first_qubit) % 2 == 0]

    second_qubit=(first_qubit+1)%N
    filter_0 = basis[(basis >> second_qubit) % 2 == 0]

    filter1_ = np.setdiff1d(basis, filter0_)
    filter_1 = np.setdiff1d(basis, filter_0)

    filter00 = np.intersect1d(filter_0, filter0_)
    filter10 = np.intersect1d(filter_0, filter1_)
    filter01 = np.intersect1d(filter_1, filter0_)
    filter11 = np.intersect1d(filter_1, filter1_)

    mask00 = np.isin(basis, filter00)
    mask10 = np.isin(basis, filter10)
    mask01 = np.isin(basis, filter01)
    mask11 = np.isin(basis, filter11)
    masks = [mask00, mask10, mask01, mask11]

    # indeces corresponding to indexes in the D-dimensional basis
    filter00 = np.where(mask00)[0]
    filter10 = np.where(mask10)[0]
    filter01 = np.where(mask01)[0]
    filter11 = np.where(mask11)[0]
    filters = [filter00, filter10, filter01, filter11]

    return filter0_, filters, masks

@njit(parallel=True, fastmath=True)
def apply_gate(state, gate, filter00, filter01, filter10, filter11):
    """
    Optimized version of the quantum gate application using numba for JIT compilation.
    
    Parameters:
    - state: ndarray, the full state vector.
    - gate: ndarray, a 4x4 complex matrix representing the quantum gate.
    - filter00, filter01, filter10, filter11: integer arrays representing the indices for splitting the state.

    Returns:
    - state_fin: ndarray, the resulting state vector after applying the gate.
    """
    # Initialize the output state
    state_fin = np.zeros_like(state, dtype=np.complex128)

    # First loop: Process filter00 and filter11
    for i in prange(len(filter00)):
        i0, i3 = filter00[i], filter11[i]
        s0, s3 = state[i0], state[i3]
        state_fin[i0] = gate[0, 0] * s0
        state_fin[i3] = gate[3, 3] * s3

    # Second loop: Process filter01 and filter10
    for i in prange(len(filter01)):
        i1, i2 = filter01[i], filter10[i]
        s1, s2 = state[i1], state[i2]
        t1 = gate[1, 1] * s1 + gate[1, 2] * s2
        t2 = gate[2, 1] * s1 + gate[2, 2] * s2
        state_fin[i1] = t1
        state_fin[i2] = t2

    return state_fin

def apply_U(state, gates, gate_ordering_idx_list, masks_dict):
    '''
    Apply the Floquet operator to the state psi 2-qubit gate at a time

    Parameters:
    - state: state vector on full Hilbert space
    - gates: list of matrices. each is a 2-qubit gate
    - gate_ordering_idx_list: list of indeces correspoding to the
                              order the gates wil be applied:
                              eg. i -> gate_{i,i+1}
    - masks_dict: dictionary containing N masks defining how a gate on
                  2 consecutive sites needs to be applied
    '''
    for gate_idx, order_idx in enumerate(gate_ordering_idx_list):
        state = apply_gate(state, gates[gate_idx], *masks_dict[order_idx])
    return state

def gen_gates_order(N, geometry='random', boundary_conditions='PBC', eo_first='True'):
    # Generate the order the gates will be applied
    if geometry == 'random':
        if boundary_conditions == 'PBC':
            return rd.sample([n for n in range(N)],N)
        elif boundary_conditions == 'OBC':
            return rd.sample([n for n in range(N-1)],N-1)
    if geometry != 'brickwork':
        raise ValueError('Only random and brickwork geometries are supported')
    gate_ordering_idx_list = []
    if eo_first:
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
    if not eo_first:
        for n in range(N):
            if n % 2 == 0:
                if n == N-1 and boundary_conditions == 'OBC':
                    continue
                else:
                    gate_ordering_idx_list.append(n)

    return np.array(gate_ordering_idx_list, dtype=int)

@njit(parallel=True, fastmath=True)
def expectation(psi1, sz, psi2):
    s = 0 
    for el in prange(len(psi1)):
        s += np.conj(psi1[el]) * sz[el] * psi2[el]
    return s