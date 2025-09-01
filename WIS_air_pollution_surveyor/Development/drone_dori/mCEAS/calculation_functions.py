import csv
import math
import numpy as np


def load_wavelengths_and_average_I_from_spectrometer_csv(filename="",sep="\t",data_begin_str="Begin Spectral Data"):
    def find_idxs_in_csv(csv_file_as_list,data_begin_str=data_begin_str):
        wavelengths_i,data_i = -10,-10
        for i,row in enumerate(csv_file_as_list[:15]):
            if len(row)<=0: continue
            if data_begin_str in row[0]:
                wavelengths_i,data_i = i+1,i+2
                break
        return data_i,wavelengths_i    
    def get_I_data_from_row(row): # Assuming same format - two fisrt cells are of timestamp
        I = row[0][row[0].index(sep)+2:]
        I = I[I.index(sep)+2:]
        return np.fromstring(I, sep="\t")
    file = open(filename, 'r')
    I_list = list(csv.reader(file))
    data_i,wavelengths_i = find_idxs_in_csv(I_list,data_begin_str=data_begin_str)
    wavelengths = np.fromstring(I_list[wavelengths_i][0], sep=sep)
    I = [get_I_data_from_row(I_list[data_i])]
    I_rows = I_list[data_i+1:]
    for row_i in I_rows:
        try:
            I_row = get_I_data_from_row(row_i)
            if I_row.shape == I[0].shape: I.append(I_row)
        except Exception as e:
            print(f"Could not get data from row {row_i}: {e}")
    I = np.stack(I).mean(0)
    return wavelengths,I

def calculate_N_air(P,T):
    Rg,N_Av = 83144.626,6.022e23 # cm^3*mbar/K/mole, molec/mole
    Rg = Rg/N_Av # cm^3*mbar/K/molec
    return P/(Rg*T) # molec/cm^3, P in mbar, T in K

def sample_y_at_x(y0_at_x0,x0,x1):
    # Adapted from https://stackoverflow.com/questions/2566412/find-nearest-value-in-numpy-array
    def find_nearest(array,value):
        idx = np.searchsorted(array, value, side="left")
        if idx > 0 and (idx == len(array) or math.fabs(value - array[idx-1]) < math.fabs(value - array[idx])):
            return idx-1
        return idx
    y0_at_x1 = []
    for x in x1:
        y0_at_x1.append(y0_at_x0[find_nearest(x0,x)])
    return np.array(y0_at_x1)

def load_sigma_from_csv(filename,w_start=250,w_end=800,eps=None):
    # assuming all first rows have some wierd strings, and each row is ["wavelangth","sigma(w)"]
    sigma_file = open(filename, 'r')
    sigma_list = list(csv.reader(sigma_file))[1:]    
    w_first = math.floor(float(sigma_list[0][0]))
    w_last = math.ceil(float(sigma_list[-1][0]))
    ws_before,ws_after = list(range(w_start,w_first+1)),list(range(w_last,w_end+1))
    sigmas_from_rows_list = [float(row[1]) for row in sigma_list]
    if eps is None: eps = np.array(sigmas_from_rows_list).min()/1000
    wavelengths = [w for w in ws_before] + [float(row[0]) for row in sigma_list] + [w for w in ws_after]
    sigmas = [eps]*len(ws_before) + sigmas_from_rows_list + [eps]*len(ws_after)
    return np.array(wavelengths),np.array(sigmas)

def calculate_Rayleigh(gas_name,w):
    if gas_name=="N2": coef1,coef2=1.2577e-15,-4.1814
    if gas_name=="He": coef1,coef2=1.336e-17,-4.1287
    if gas_name=="O2": coef1,coef2=1.0455e-15,-4.1814
    return coef1*(w**coef2)

def calculate_alpha_water(RH,P,T,sigma_H2O):
    # From https://www.hatchability.com/Vaisala.pdf
    t = 1-T/647.096 # T in K
    P_water = math.exp((-7.85951783*t+1.84408259*t**1.5-11.7866497*t**3+22.6807411*t**3.5 +
                        -15.9618719*t**4+1.80122502*t**7.5)*(647.096/T))*RH*220640/100
    N_air = calculate_N_air(P,T)
    N_water = N_air*P_water/(P-P_water)
    return N_water*sigma_H2O

def calculate_alpha_Rayleigh_air(w,P,T):
    # Assuming alpha_Rayleigh of air is composed only of 78% N2 and 22% O2
    N_air = calculate_N_air(P=P,T=T)
    sigma_Rayleigh_N2 = calculate_Rayleigh("N2",w)
    sigma_Rayleigh_O2 = calculate_Rayleigh("O2",w)
    alpha_Rayleigh_air = 0.78*N_air*sigma_Rayleigh_N2+0.22*N_air*sigma_Rayleigh_O2
    return alpha_Rayleigh_air
 