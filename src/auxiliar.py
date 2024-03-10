import matplotlib.pyplot as plt
import numpy as np

def plot_fits(data, min=1, max=97):
    vmin, vmax = np.percentile(data, [min, max])
    
    plt.imshow(data, cmap='gray', vmin=vmin, vmax=vmax)
    plt.show()
    
    