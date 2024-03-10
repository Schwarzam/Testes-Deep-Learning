import matplotlib.pyplot as plt
import numpy as np

def plot_fits(data, min=1, max=97, ax = None):
    vmin, vmax = np.percentile(data, [min, max])
    
    if ax is not None:
        ax.imshow(data, cmap='gray', vmin=vmin, vmax=vmax)
    else:
        plt.imshow(data, cmap='gray', vmin=vmin, vmax=vmax)
        plt.show()
        
    