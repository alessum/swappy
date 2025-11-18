import numpy as np
import functions as fn
import matplotlib.pyplot as plt
import numpy.linalg as npla
import scipy.linalg as la
import scipy.special as spsp
import pickle, sys, os, shutil
from scipy.ndimage import gaussian_filter1d
# import pretty_errors
import pandas as pd
terminal_width, _ = shutil.get_terminal_size()

# N=15: output/N15/POLFED/JzPi/*Jz0,78*eigvec*
# N=16: output/N16/POLFED/N16_J0,*Jz0,78*eigvec*
from scipy.special import comb, digamma

def page_entropy(d1, d2):
    """
    Compute the exact Page entropy for bipartite dimensions d1 and d2.
    """
    if d1 > d2:
        d1, d2 = d2, d1
    if d1 == 0:
        return 0.0
    return digamma(d1 * d2 + 1) - digamma(d2 + 1) - (d1 - 1) / (2 * d2)

def constrained_page_value(L, N, L_A):
    """
    Compute the correct Page value (average entanglement entropy) 
    for random pure states in the fixed magnetization subsector 
    for arbitrary L (total sites), N (total particles/up-spins), L_A (subsystem A sites).
    
    Note: Uses float computations; for very large L (>~300), binomial coefficients may overflow.
    In such cases, use asymptotic approximations instead.
    """
    L_B = L - L_A
    min_NA = max(0, N - L_B)
    max_NA = min(L_A, N)
    D = comb(L, N)
    S = 0.0
    term_psi = 0.0
    psi_D = digamma(D + 1)
    for NA in range(min_NA, max_NA + 1):
        dA = comb(L_A, NA)
        dB = comb(L_B, N - NA)
        d = dA * dB
        lambda_ = d / D
        S_NA = page_entropy(dA, dB)
        S += lambda_ * S_NA
        term_psi += lambda_ * digamma(d + 1)
    S += psi_D - term_psi
    return S


fn.begin()
time_elapsed = 0.0
############################################################################
tic = fn.tic("Load data")
############################################################################

csv_file_name = '2025'
df = pd.read_csv(os.getcwd() +
                 "/data/eigvec_entanglement_data/"+csv_file_name+".csv")

#######################################
############################################################################
# sys.argv[1:] = sys.argv[1:][::-1]
data_list = []
numb_rnd_instances = skipped = 0
if len(sys.argv[1:]) == 0:
    raise Exception("No data files were input")
elif len(sys.argv[1:]) > 0:
    for i in range(len(sys.argv[1:])):
        with open(sys.argv[1:][i], 'rb') as f:
            data = pickle.load(f)
            if len(data) == 3 and 'entanglement' in sys.argv[1:][i]:
                data_list.append(data)
project_dir_path = os.path.dirname(__file__)

#######################################
toc = fn.toc(tic)
time_elapsed += toc - tic
############################################################################
tic = fn.tic("Averaging data")
############################################################################

spin_profiles = []
spin_pdfs = []
first_t_list = data_list[0][1]
N_old = None
num_states_per_rd_instance_old = None
M, J, Jz, N = None, None, None, None
a = 20
b = a

def calc(data):
    global N_old
    global num_states_per_rd_instance_old
    global M, J, Jz, N

    params = data[0]
    
    # Extract input parameter values for this data file
    N = params['N']
    J = np.round(params['J'], 3)
    Jz = np.round(params['Jz'], 3)
    M = params['magnetization']
    if N_old is not None:
        assert N_old == N, 'N is not the same for all data files'

    N_old = N   
    
    numb_spin_up = N//2 if N % 2 == 0 else (N//2)+1
    NA = N//2

    # print("Calculating Page value for L =", N,
    #       ", N_up =", numb_spin_up,
    #       ", L_A =", NA)
    page_value = constrained_page_value(N, numb_spin_up, NA)

    # print("Page value:", page_value)
    
    eigvec_entanglement_list = data[2] / page_value

    eigvec_entanglement_mean = np.mean(eigvec_entanglement_list)
    num_states_per_rd_instance = len(eigvec_entanglement_list)
    
    
    # if N_old is not None:
    #     assert num_states_per_rd_instance_old == num_states_per_rd_instance, 'num_states_per_rd_instance is not the same for all data files'

    # num_states_per_rd_instance_old = num_states_per_rd_instance


    
    return np.array([J, Jz, eigvec_entanglement_mean, num_states_per_rd_instance]);


res = np.array([calc(data) for data in data_list])

# Grouping results by J
res[:, 0] = np.round(res[:, 0], 3)
res[:, 1] = np.round(res[:, 1], 2)
unique_J_values = np.unique(res[:, 0])
print('unique_J_values:', len(unique_J_values))
unique_Jz_values = np.unique(res[:, 1])
print('unique_Jz_values:', len(unique_Jz_values))
unique_num_states = np.unique(res[:, 3])
print('unique_num_states:', unique_num_states)

def remove_outliers_and_average(values, a, b):
    '''Convert to numpy array for easier manipulation'''
    values = np.array(values)
    # Calculate the a-th percentile and the (100-b)-th percentile
    lower_bound = np.percentile(values, a)
    upper_bound = np.percentile(values, 100 - b)
    # Filter out the outliers
    filtered_values = values[(values >= lower_bound) & (values <= upper_bound)]
    # Compute the average of the remaining values
    average = np.mean(filtered_values)
    std = np.std(filtered_values)
    num_rd_instances = len(filtered_values)
    thrown_instances = len(values) - num_rd_instances
    return average, std, num_rd_instances, thrown_instances

def remove_outliers_and_average(values, multiplier=1.5):
    '''Convert to numpy array for easier manipulation'''
    values = np.array(values)
    
    if len(values) == 0:
        return np.nan, np.nan, 0, 0
    
    # Calculate Q1 (25th percentile) and Q3 (75th percentile)
    q1 = np.percentile(values, 25)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    
    # Define bounds
    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr
    
    # Filter out the outliers
    filtered_values = values[(values >= lower_bound) & (values <= upper_bound)]
    
    # Compute the average and std of the remaining values
    average = np.mean(filtered_values) if len(filtered_values) > 0 else np.nan
    std = np.std(filtered_values) if len(filtered_values) > 0 else np.nan
    num_rd_instances = len(filtered_values)
    if len(values) != num_rd_instances:
        thrown_instances = len(values) - num_rd_instances
    else:
        thrown_instances = 0
    
    return average, std, num_rd_instances, thrown_instances

for J in unique_J_values:
    for Jz in unique_Jz_values:
        indices = np.where((res[:, 0] == J) & (res[:, 1] == Jz))[0]
        list_of_vne = np.array(res[indices, 2])
        avg_vne, std_vne, num_rd_instances, thrown_instances = remove_outliers_and_average(list_of_vne, 3.5)#a, b)
        print(f"J={J}, Jz={Jz} -> avg_vne={avg_vne}, std_vne={std_vne}, num_rd_instances={num_rd_instances}, thrown_instances={thrown_instances}")
        if np.isnan(thrown_instances):
            print("NaN thrown instances detected, skipping entry.")
        num_states = np.sum(res[indices, 3])
        new_df_row = {'N': N, 'J': J, 'Jz': Jz, 'magnetization': M,
                    'eigvec_entanglement_mean': avg_vne, 'eigvec_entanglement_std': std_vne, 
                    'num_states_per_rd_instance': num_states_per_rd_instance_old, 'num_rd_instances': num_rd_instances, 'thrown_instances': thrown_instances}
        
        df.loc[len(df.index)] = new_df_row

print(len(df.index))
print(df)

df.to_csv("data/eigvec_entanglement_data/"+csv_file_name+".csv",
          index=False)

#######################################
toc = fn.toc(tic)
time_elapsed += toc - tic
#######################################
print('-' * terminal_width)
print('     Total:', time_elapsed, 'seconds')
print('-' * terminal_width)
fn.finish()
#######################################



