import numpy as np
import matplotlib.pyplot as plt

def peaking(Q:float, dBgain:float, center_freq:float, samplerate:int):
    A = np.pow(10, dBgain/40)
    w0 = 2*np.pi*center_freq/samplerate
    alpha = np.sin(w0) / (2.0*Q)
    
    b0 = 1 + alpha*A
    b1 = -2*np.cos(w0)
    b2 = 1 - alpha*A
    
    a0 = 1 + alpha/A
    a1 = b1
    a2 = 1 - alpha/A

    return [b0, b1, b2], [a0, a1, a2]

def shelving(Q:float, dBgain:float, center_freq:float, samplerate:int):
    A = np.pow(10, dBgain/40)
    w0 = 2*np.pi* center_freq/samplerate
    w_cos = np.cos(w0)
    alpha = np.sin(w0) / (2.0*Q)

    b0 = A*(A+1 + (A-1)*w_cos + 2*np.sqrt(A)*alpha)
    b1 = -2*A*(A-1 + (A+1)*w_cos)
    b2 = A*(A+1 + (A-1)*w_cos - 2*np.sqrt(A)*alpha)
    
    a0 = A+1 - (A-1)*w_cos + 2*np.sqrt(A)*alpha
    a1 = 2*(A-1 - (A+1)*w_cos)
    a2 = A+1 - (A-1)*w_cos - 2*np.sqrt(A)*alpha

    return [b0, b1, b2], [a0, a1, a2]

def calculate_bandwidth(Q:float):
    return 2.0 * np.arcsinh(1.0/(2.0*Q)) / np.log10(2)