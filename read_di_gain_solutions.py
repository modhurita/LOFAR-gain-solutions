import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import pyfits

#========================
#Parameters to be entered
#------------------------
NODES = range(101,116)
OBS_ID = 'L205861'

DIRECTORY = '/net/node%s/data/users/lofareor/from_LTA/%s_002/*_002.MS.solutions' #Direction-independent sagecal solutions files. First string is node number, second is observation ID.

COLUMN_ID = 1 #Column ID in direction-independent gain solutions file: Column ID 1 refers to gain solutions for the full field, column ID 2 refers to gain solutions in the direction of 3C61 

SAMPLING_INTERVAL = 60 #Choose every SAMPLING_INTERVAL-th time sample to plot/visualize
#========================

def generate_gain_solutions_files_list(directory, nodes, obs_id):

    gain_solutions_files = []

    #Read solutions files into a list
    for node in nodes:
        files = glob.glob(directory%(node, obs_id))
        gain_solutions_files = gain_solutions_files + files

    subband_index = [x.split('_')[4] for x in gain_solutions_files]

    gain_solutions_files = list(zip(*sorted(zip(subband_index, gain_solutions_files)))[1])

    return gain_solutions_files

def read_general_parameters(gain_solutions_files):

    num_freqs = len(gain_solutions_files)

    #Open first gain solutions file
    f = open(gain_solutions_files[0])        
    for i in range(3):
        line = f.readline()
    f.close()

    parameters = line.split(' ')

    bandwidth = float(parameters[1])
    time_interval = float(parameters[2])
    num_stations = int(parameters[3])  
    num_clusters =  int(parameters[4]) 
    num_effective_clusters = int(parameters[5])

    num_lines = os.popen('wc -l %s'%gain_solutions_files[0]).read()  
    num_lines = int(num_lines.split(' ')[0])
    num_timesteps = (num_lines - 3)/(8*num_stations)

    return (bandwidth, time_interval, num_timesteps, num_stations, num_clusters, num_effective_clusters)

class Cluster:

    cluster_id = None
    chunk_size = None
    frequency_range = None
    time_range = None
    start_column_gain_sols = None

if __name__ == '__main__':
    
    # Set variables
    nodes = NODES
    obs_id = OBS_ID

    directory = DIRECTORY
    
    cluster_ids = ['1', '2'] #List of cluster IDs
    chunk_sizes = [1, 1] #Chunk sizes for clusters
    clusters = [] #List of cluster objects  
    start_column_gain_sols = [1, 2] # Start column number for each cluster

    #Choose times sampling_interval apart
    sampling_interval = SAMPLING_INTERVAL
 
   #Get list of gain solutions files    
    gain_solutions_files = generate_gain_solutions_files_list(directory, nodes, obs_id)
          
    # Read several parameters
    (bandwidth, time_interval, num_timesteps, num_stations, num_clusters, num_effective_clusters) = read_general_parameters(gain_solutions_files)

    # Determine and assign some attributes of cluster objects
    for i in range(len(cluster_ids)):
        cluster = Cluster()
        cluster.cluster_id = cluster_ids[i]
        cluster.chunk_size = chunk_sizes[i]
        cluster.start_column_gain_sols = start_column_gain_sols[i]
        clusters.append(cluster)

    #solution time in minutes
    for i in range(len(clusters)):
        time_range = [sampling_interval*k*time_interval/chunk_sizes[i] for k in range(chunk_sizes[i]*(num_timesteps/sampling_interval+1))]
        clusters[i].time_range = time_range

    freq_range = []
    for filename in gain_solutions_files:

        f = open(filename)  
        for i in range(3):
            line = f.readline()
        f.close()
        
        freq = line.split(' ')[0]
        freq_range.append(float(freq))  
    num_freqs = len(freq_range)

    #frequency range for solutions
    for cluster in clusters:
        cluster.freq_range = freq_range
   
    #Create nested dictionary to store data
    #data[cluster id][station index][frequency index][time index][jones term]

    #Cluster ID of cluster data to be read
    this_cluster_id = str(COLUMN_ID)
    data = {}
    for i1 in range(num_clusters):

      if cluster_ids[i1] == this_cluster_id:
        cluster_num = i1
        data[cluster_ids[i1]] = {}
        for i2 in range(num_stations):
            data[cluster_ids[i1]][i2] = {}
            for i3 in range(num_freqs):
                data[cluster_ids[i1]][i2][i3] = {}
                for i4 in range(len(clusters[i1].time_range)):
                    data[cluster_ids[i1]][i2][i3][i4] = {}

    total_rows = num_stations*num_timesteps*8 + 3
    total_columns = num_effective_clusters

    for i in range(len(gain_solutions_files)):
        f = open(gain_solutions_files[i])
        for j in range(total_rows):
            l1 = f.readline()
            l1 = l1.rstrip('\n')
            l1 = l1.split(' ')
            l1 = l1[0:1] + l1[2:]
            line = l1

            if j>2: #row number > 2
                row_num = int(line[0])       
                time_int = (j-3)/(8*num_stations)
                station_num = row_num/8
                jones_code = 'S%s'%str(row_num%8)
 
                if time_int%sampling_interval==0:

                    k=cluster_num
                    time_step = time_int/sampling_interval 
                    data[cluster_ids[k]][station_num][i][time_step][jones_code] = float(line[cluster_num+1]) 

        f.close()
    
    np.savez('di_data_obsid_%s_column_%s.npz'%(obs_id, cluster_ids[cluster_num]), data=data, cluster_id=cluster_ids[cluster_num], num_stations=num_stations, freq_range=freq_range, time_range=clusters[cluster_num].time_range)   

    
       
   
    
   
