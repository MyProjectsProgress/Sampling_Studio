# ------------------------------------------------------------------------------------Importing liberaries
import streamlit as st
from numpy import sin,pi,linspace,zeros,arange,mean,sqrt,random,resize,sum,sinc
import matplotlib.pyplot as plt
import pandas as pd
from scipy.signal import find_peaks
import scipy.fft
import numpy as np
# ------------------------------------------------------------------------------------Setting Global Variables
list_of_objects = []    #Contains objects created from Signal class

# ------------------------------------------------------------------------------------Signal class that contains the frequency and amplitude of each signal
class Signal:
    def __init__(self,amplitude,frequency):
        self.amplitude = amplitude 
        self.frequency = frequency

# ------------------------------------------------------------------------------------Adding Signals: Contains the sliders that creates sin waves then sum them with the uploaded signal and remove them and returns the total signals
def add_signal(df):
    global total_signals

    list_of_columns = df.columns
    df_y_axis = df[list_of_columns[1]]
    corresponding_x_axis = linspace(0,2, len(df_y_axis))

    if len(list_of_objects)==0: 
        total_signals = df_y_axis
    else:
        total_signals = df_y_axis
        for object in list_of_objects:
            object_frequency = object.frequency
            object_amplitude = object.amplitude
            signal_y_axis = object_amplitude*sin(2*pi*object_frequency*corresponding_x_axis)
            total_signals += signal_y_axis

    col1,col2 = st.sidebar.columns(2)
    col11,col22,col33 = st.sidebar.columns([4,1,1])
    with col1:
        frequency = st.slider('Frequency (Hz)', min_value=1, max_value=50, step=1, key='frequency Box')
    with col2: 
        amplitude = st.slider('Amplitude (Volt)', min_value=1, max_value=50, step=1, key='Amplitude Box') 

    with col22:
        add_button = st.button('Add', key="Save Button") 
    if add_button:
        total_signals = adding_sin_waves(frequency,amplitude,df_y_axis,corresponding_x_axis)

    signals_menu = [] 
    splitting_menu_contents = [] 
    for object in list_of_objects: 
        signals_menu.append(f'Freq: {object.frequency} Amp: {object.amplitude}') 
    with col11:
        signals_names = st.selectbox('Your Signals',signals_menu) 
    splitting_menu_contents = str(signals_names).split(' ')
    if len(splitting_menu_contents)==4:  
        removed_signal_freq = float(splitting_menu_contents[1]) 
        removed_signal_amp = float(splitting_menu_contents[3]) 

    with col33:
        remove_button = st.button('Delete', key="Remove Button") 

    if remove_button and len(list_of_objects)>0:
        total_signals = removing_sin_waves(df,removed_signal_freq,removed_signal_amp) 
        st.experimental_rerun()
    return total_signals

# ------------------------------------------------------------------------------------Sampling total signals after adding noise or adding sin waves or even deleting one or more signal and returning the reconstructed signal to dowonload it
def signal_sampling(df,added_signals):
    contain = st.container()
    col1,col2 = st.sidebar.columns(2)
    column1,column2,column3,column4 = st.columns(4)
    with column1:
        original_graph_checkbox = col1.checkbox('Original Signal',value=True, key='Original_Graph 2001')
    with column2:
        interpolation_checkbox  = col1.checkbox('Interpolation', key='interpolation_check_box 2002')
    with column3:
        noise_checkbox          = col2.checkbox('Add Noise', key="Noise Check Box 2003")
    with column4:
        sampling_checkbox       = col2.checkbox("   Sampling Points", key='2004')

    # Getting df x_axis and y_axis
    list_of_columns = df.columns
    df_y_axis = (df.iloc[:,1]).to_numpy()
    df_x_axis = (df.iloc[:,0]).to_numpy()
    added_signals = added_signals.to_numpy()

    # Frequency domain representation
    amplitude = np.abs(scipy.fft.rfft(added_signals))
    frequency = scipy.fft.rfftfreq(len(df_y_axis), (df_x_axis[1]-df_x_axis[0]))
    indices = find_peaks(amplitude)
    if len(indices[0])>0 :
        max_freq=round(frequency[indices[0][-1]])
    else:
        max_freq=1   

    if sampling_checkbox or interpolation_checkbox  :
        sampling_options = st.sidebar.selectbox('Sampling Frequency Options' ,["Actual Sampling Frequency", f"Sampling Relative to Max Frequency: {max_freq} Hz"], key="Options")
        if sampling_options == "Actual Sampling Frequency":
            sample_freq = st.sidebar.slider(label= "",min_value=1,max_value=100,value=1,step=1)
        else:
            sample_freq = max_freq * st.sidebar.slider(label= "",min_value=1,max_value=10,value=1,step=1)
    else:
        sample_freq = 1

    list_of_columns = df.columns
    df_x_axis = list(df[list_of_columns[0]])

    begin_time = df[list_of_columns[0]].iat[0] # begin_time
    end_time = df[list_of_columns[0]].iloc[-1] # end time 

    time_range = abs(begin_time - end_time)

    sample_step = int((len(df_x_axis)/time_range)/(sample_freq)) #taking samples using steps

    sampled_time = df_x_axis[::sample_step] #list from beign to end of x-axis with step of sample Rate

    #Pass array of points , number of rows , number of columns to time_matrix
    time_points = list(df[list_of_columns[0]])
    time_matrix = resize(time_points, (len(sampled_time), len(time_points))) # Matrix containing all Timepoints
    
    # The following equations is according to black- Shannon interpoltion formula ((t- nT)/T)
    plotted_matrix = (time_matrix.T - sampled_time) / (sampled_time[1] - sampled_time[0]) # Transpose for time_matrix is a must for proper calculations (broadcasting)

    if noise_checkbox:
        #------------------------------ Adding and sampling noise ----------------------------------------#
        noised_signal = add_noise()
        total_signals=list(noised_signal)
        sampled_signals = total_signals[::sample_step]
        #------------------------------ Reconstructed signals of noise ------------------------------------#
        final_matrix = sampled_signals * sinc(plotted_matrix)
    else:
        #------------------------------ Sampling signals without noise ------------------------------------#
        total_signals = list(added_signals)
        sampled_signals = total_signals[::sample_step]
        #------------------------------ Reconstruct noise signal with noise -------------------------------#
        final_matrix = sampled_signals * sinc(plotted_matrix)

    reconstructed_signal = sum(final_matrix, axis=1)

    #---------------------------------- Signal Plotting ---------------------------------------------------#
    fig, axs = plt.subplots()
    fig.set_size_inches(14,5)

    if interpolation_checkbox :
        axs.plot(time_points,reconstructed_signal,color='red',alpha=1,label="Reconstructed",linewidth=2)
    
    if original_graph_checkbox:
        axs.plot(time_points,total_signals, color='darkslategrey',alpha=0.5,label="Original")
    
    if sampling_checkbox:
        axs.plot(sampled_time, sampled_signals, color='black' , marker="o" ,linestyle="" ,alpha=0.8,label="Sampled",markersize=4)

    x_zero_line = linspace(0,end_time,1000)
    y_zero_line = zeros(1000)
    axs.plot(x_zero_line , y_zero_line, color='grey', alpha = 0.2)

    plt.xlim(0,end_time)
    font1 = {'family':'serif','color':'black','size':20}
    plt.xlabel("Time (Seconds)",fontdict = font1)
    plt.ylabel("Amplitude (Volt)",fontdict = font1)
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5,0.5,0.7),fontsize = 11)
    contain.plotly_chart(fig,use_container_width=True)

    return reconstructed_signal,end_time,begin_time

# ------------------------------------------------------------------------------------Adding Noise to signal then returning the noised signal
def add_noise():
    global noise
    SNR = st.sidebar.slider(label='SNR', min_value=1, max_value=50, value=1, step=1)
    signal_power = total_signals **2                                    # Generating the signal power
    signal_power_avg = mean(signal_power)                               # mean of signal power
    if (SNR==0):
        noise_power = signal_power_avg / 0.00001
    else:
        noise_power = signal_power_avg / SNR
    mean_noise = 0
    noise = random.normal(mean_noise,sqrt(noise_power),len(total_signals))
    noise_signal = total_signals + noise
    return noise_signal

# ------------------------------------------------------------------------------------Adding Sin Waves
def adding_sin_waves(frequency,amplitude,df_y_axis,corresponding_x_axis):
    total_signals = df_y_axis
    list_of_objects.append(Signal(frequency=frequency, amplitude=amplitude))
    for object in list_of_objects:
        object_frequency = object.frequency
        object_amplitude = object.amplitude
        signal_y_axis = object_amplitude*sin(2*pi*object_frequency*corresponding_x_axis)
        total_signals += signal_y_axis
    return total_signals

# ------------------------------------------------------------------------------------Removing Sin Waves
def removing_sin_waves(df,removed_freq,removed_amp):
    list_of_columns = df.columns
    df_y_axis = df[list_of_columns[1]]
    corresponding_x_axis = linspace(0, 2, len(df_y_axis))
    total_signals = df_y_axis
    for object in list_of_objects:
        if removed_freq == object.frequency and removed_amp == object.amplitude:
            list_of_objects.remove(object)
            break
    for object in list_of_objects:
        object_frequency = object.frequency
        object_amplitude = object.amplitude
        signal_y_axis = object_amplitude*sin(2*pi*object_frequency*corresponding_x_axis)
        total_signals += signal_y_axis
    return total_signals