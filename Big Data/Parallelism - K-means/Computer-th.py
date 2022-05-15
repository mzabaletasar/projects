import threading as th
import pandas as pd
import numpy as np
from sklearn import preprocessing
from kneed import KneeLocator
import matplotlib.pyplot as plt
import time
import collections


def algorithm(k):
    df = pd.read_csv('computers.csv')
    df['cd'] = pd.get_dummies(df['cd']).drop('no', axis=1)
    df['laptop'] = pd.get_dummies(df['laptop']).drop('no', axis=1)
    df.pop('id')
    x = df.values
    min_max_scaler = preprocessing.MinMaxScaler()
    x_scaled = min_max_scaler.fit_transform(x)
    df = pd.DataFrame(x_scaled, columns=df.columns)
    
    centroids = []
    for i in range(k):
        centroids.append(np.random.random(df.shape[1]))
    convg_result = False
    i = 1
    while convg_result == False:
        
        df_distancias = pd.DataFrame(columns=list(map(str,range(k))))
        j=0
        if i==1:  
            for centroid in centroids:
                df_distancias[str(j)] = np.sqrt((np.square(df.sub(np.array(centroid)))).sum(axis=1)).values
                j=j+1
        else:
            for centroid in new_centroids:
                df_distancias[str(j)] = np.sqrt((np.square(df.loc[:,df.columns[:-1]].sub(np.array(centroid)))).sum(axis=1)).values
                j=j+1
        
        cluster_assignment = np.argmin(df_distancias.to_numpy(), axis=1)+1

        df['cluster'] = cluster_assignment
        
        new_centroids = []
        for clust in range(1,k+1):
            if len(df.loc[df['cluster']==clust, df.columns[:-1]]) == 0:
                new_centroids.append(centroids[clust-1])
            else:
                new_centroids.append(np.mean(df.loc[df['cluster']==clust, df.columns[:-1]], axis=0))
                
        df_distancias = pd.DataFrame(columns=list(map(str,range(k))))
        j=0
        for centroid in new_centroids:
            df_distancias[str(j)] = np.sqrt((np.square(df.loc[:,df.columns[:-1]].sub(np.array(centroid)))).sum(axis=1)).values
            j=j+1
        
        new_assignment = np.argmin(df_distancias.to_numpy(),axis=1)+1
        num_cambios = (df['cluster'] - new_assignment).astype(bool).sum(axis=0)
        convg_result = num_cambios < (0.05 * df.shape[0])
        i = i+1

    sse_list = []    
    for clust in range(1,k+1):
        sse_list.append(np.sum(np.sum((df.loc[df['cluster']==clust,
                                               df.columns[:-1]] - new_centroids[clust-1] )**2)))
    sse = np.sum(sse_list)
    df.pop('cluster')
    sse_points.append(sse)
    
def read_and_scale_chunk(i): 
    df = pd.read_csv('computers.csv', 
                 skiprows=i, nrows=int(500000/num_chunks), header=None)
    df = df.rename(columns={0:'id', 1:'price', 2:'speed',
                            3:'hd', 4:'ram', 5:'screen',
                            6:'cores', 7:'cd', 8:'laptop',
                            9:'trend'})
    df['cd'] = pd.get_dummies(df['cd']).drop('no', axis=1)
    df['laptop'] = pd.get_dummies(df['laptop']).drop('no', axis=1)
    
    x = df.values 
    min_max_scaler = preprocessing.MinMaxScaler()
    x_scaled = min_max_scaler.fit_transform(x)
    df = pd.DataFrame(x_scaled, columns=df.columns)
    df_chunks.append(dict({df.iloc[1,1]:df}))
    
def calculate_dist_chunk(centroid,chunk):  
    cluster_assignment_chunk.append(dict({chunk.iloc[1,1] : np.sqrt((np.square(chunk.loc[:,chunk.columns[1:]].sub(np.array(centroid)))).sum(axis=1)).values}))

sse_points = []
df_chunks = []
num_chunks = 5

if __name__=='__main__':
    
    st = time.time()
    threads = []
    max_clusters = 10

    for k in range(1,max_clusters+1):
        t = th.Thread(target=algorithm, args = [k])
        t.start()
        threads.append(t)
       
    for thread in threads[0:max_clusters]:
        thread.join() 
    
    ejex = range(1,len(sse_points)+1)

    kn = KneeLocator(ejex, sse_points, curve='convex', direction='decreasing')
    print('The optimal number of clusters (k) is:', kn.knee)

    print('Clustering now with optimal k ...')    
    num_clusters = kn.knee
    centroids = []
    for i in range(num_clusters):
        centroids.append(np.random.random(9))
    
    for k in [int(j*500000/num_chunks)+1 for j in range(num_chunks)]:
        t = th.Thread(target=read_and_scale_chunk, args = [k])
        t.start()
        threads.append(t)
        
    for thread in threads[max_clusters:]:
        thread.join()
    
    flat_dict = {}
    for d in df_chunks:
        flat_dict.update(d)
    ordered_dict = collections.OrderedDict(sorted(flat_dict.items()))
    df_chunks = list(ordered_dict.values())
    
    convg_result = False
    i = 1
    while convg_result == False:

        cluster_assignment = []
        df_distancias = pd.DataFrame(columns=list(map(str,range(num_clusters))))
        j=0
        if i==1:
            for centroid in centroids:
                cluster_assignment_chunk = []

                for chunk in df_chunks:
                    t = th.Thread(target=calculate_dist_chunk, args = (centroid,chunk))
                    t.start()
                    threads.append(t)
                    
                for thread in threads[-len(df_chunks):]:
                    thread.join()
                
                flat_dict = {}
                for d in cluster_assignment_chunk:
                    flat_dict.update(d)
                ordered_dict = collections.OrderedDict(sorted(flat_dict.items()))
                cluster_assignment_chunk = list(ordered_dict.values())
                
                df_distancias[str(j)] = [item for sublist in cluster_assignment_chunk for item in sublist]
                j=j+1
        else:
            for centroid in new_centroids: 
                cluster_assignment_chunk = []

                for chunk in df_chunks:
                    t = th.Thread(target=calculate_dist_chunk, args = (centroid,chunk))
                    t.start()
                    threads.append(t)
                    
                for thread in threads[-len(df_chunks):]:
                    thread.join()
                    
                flat_dict = {}
                for d in cluster_assignment_chunk:
                    flat_dict.update(d)
                ordered_dict = collections.OrderedDict(sorted(flat_dict.items()))
                cluster_assignment_chunk = list(ordered_dict.values())
                
                df_distancias[str(j)] = [item for sublist in cluster_assignment_chunk for item in sublist]
                j=j+1
        

        cluster_assignment = np.argmin(df_distancias.to_numpy(), axis=1)+1 
        df = pd.concat(df_chunks)
        
        df['cluster'] = cluster_assignment
        df.pop('id')
        new_centroids = []
        for clust in range(1,num_clusters+1):
            
            if len(df.loc[df['cluster']==clust, df.columns[:-1]]) == 0:
                new_centroids.append(centroids[clust-1])
            else:
                new_centroids.append(np.mean(df.loc[df['cluster']==clust, df.columns[:-1]], axis=0))
                
        df_distancias = pd.DataFrame(columns=list(map(str,range(num_clusters)))) # starts convergence criteria
        j=0
        for centroid in new_centroids:
            df_distancias[str(j)] = np.sqrt((np.square(df.loc[:,df.columns[:-1]].sub(np.array(centroid)))).sum(axis=1)).values
            j=j+1
        
        new_assignment = np.argmin(df_distancias.to_numpy(),axis=1)+1
        num_cambios = (df['cluster'] - new_assignment).astype(bool).sum(axis=0)
        convg_result = num_cambios < (0.05 * df.shape[0])
        i = i+1

    et = time.time()
    print('Total execution time:', et-st)
    
    
    # Plot first 2 dimensions of clusters
    for k in range(1,num_clusters+1):
        plt.scatter(df.loc[df['cluster']==k,'price'], df.loc[df['cluster']==k,'speed'], label = k,s=3)
    plt.legend()
    plt.show()
    
    # Cluster with highest average price:
    df_og = pd.read_csv('computers.csv')
    df_og.pop('id')
    data = df_og.values
    ma=np.max(data[:,0])
    mi=np.min(data[:,0])
    print('Cluster', df.groupby('cluster')['price'].mean().idxmax(),
          'has the highest average price of:', df.groupby('cluster')['price'].mean().max()*(ma-mi)+mi)

    # Plot heat map
    fig, ax = plt.subplots()
    im = ax.imshow(new_centroids, cmap='hot_r', interpolation = 'nearest')
    ax.set_xticks(np.arange(len(df.columns[:-1])))
    ax.set_yticks(np.arange(len(range(1,num_clusters+1))))
        
    ax.set_xticklabels(df.columns[:-1])
    ax.set_yticklabels(range(1,num_clusters+1))
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')
    
    ax.set_title('Centroids Heatmap')
    fig.tight_layout()
    cbar=plt.colorbar(im)
    cbar.ax.get_yaxis().set_ticks([])
    for j, lab in enumerate(['lowest\n value','','','','','','','','highest\n value']):
        cbar.ax.text(1.2, (0.75 * j + 0.3) / 8.0, lab)
    cbar.ax.get_yaxis().labelpad = 15

    # Plot of Elbow graph:
    plt.figure(figsize=(16,8))
    plt.plot(ejex, sse_points, 'bx-')
    plt.xlabel('num of clusters')
    plt.ylabel('Sum of Squared Distances')
    plt.title('Elbow graph')
    plt.show()

