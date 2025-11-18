import numpy as np
import functions as fn
import matplotlib.pyplot as plt
import numpy.linalg as npla
import scipy.linalg as la
import scipy.special as spsp
import pickle, sys, os, shutil
from scipy.ndimage import gaussian_filter1d
import pretty_errors
import pandas as pd
terminal_width, _ = shutil.get_terminal_size()

# N=15: output/N15/POLFED/JzPi/*Jz0,78*eigvec*
# N=16: output/N16/POLFED/N16_J0,*Jz0,78*eigvec*


fn.begin()
time_elapsed = 0.0
############################################################################
tic = fn.tic("Load data")
############################################################################

csv_file_name = 'second'
df = pd.read_csv(os.getcwd() +
                 "/data/gap_ratio_data/"+csv_file_name+".csv")

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
a = 0
b = a

def calc(data):
    global N_old
    global num_states_per_rd_instance_old
    global M, J, Jz, N

    params = data[0]
    eigphases = data[1]
    level_spacings = (eigphases[1:] - eigphases[:-1])

    gap_ratios = []
    for j in range(len(level_spacings) - 1):
        gap_ratios.append(min([level_spacings[j], level_spacings[j+1]])/
                    max([level_spacings[j], level_spacings[j+1]]))

    gap_ratio_mean = np.mean(gap_ratios)
    num_states_per_rd_instance = len(eigphases)

    # Extract input parameter values for this data file
    N = params['N']
    J = np.round(params['J'], 3)
    Jz = np.round(params['Jz'], 3)
    M = params['magnetization']
    if N_old is not None:
        assert N_old == N, 'N is not the same for all data files'
        assert num_states_per_rd_instance_old == num_states_per_rd_instance, 'num_states_per_rd_instance is not the same for all data files'

    N_old = N   
    num_states_per_rd_instance_old = num_states_per_rd_instance
    
    return np.array([J, Jz, gap_ratio_mean, num_states_per_rd_instance]);


res = np.array([calc(data) for data in data_list])

# Grouping results by J
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

for J in unique_J_values:
    for Jz in unique_Jz_values:
        indices = np.where((res[:, 0] == J) & (res[:, 1] == Jz))[0]
        list_of_gap = np.array(res[indices, 2])
        avg_gap, std_gap, num_rd_instances, thrown_instances = remove_outliers_and_average(list_of_gap, a, b)
        num_states = np.sum(res[indices, 3])
        new_df_row = {'N': N, 'J': J, 'Jz': Jz, 'magnetization': M,
                    'gap_ratio_mean': avg_gap, 'gap_ratio_std': std_gap, 
                    'num_states_per_rd_instance': num_states_per_rd_instance_old, 'num_rd_instances': num_rd_instances, 'thrown_instances': thrown_instances}
        
        df.loc[len(df.index)] = new_df_row

print(len(df.index))
print(df)

df.to_csv("data/gap_ratio_data/"+csv_file_name+".csv",
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



