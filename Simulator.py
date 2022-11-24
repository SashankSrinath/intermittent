# Interpolation in milliseconds?
# Prediction of voltage depending on value ( say we need 2V after discharge )
# Automation of tasks to be done ( maybe with reading some csv )
# How much to sleep to finish task in one shot
# Try to change pmax to a lesser value, slopes to higher value


import csv, sys
import numpy
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import datetime

V_max = 3.3 # Device max voltage
V_min = 1.8 # Device min voltage
C = 0.5 # Capacitance in Farad
pmax = 0.000418/4 # Datasheet of LH3 solar cell
Gstandard = 500/120 # pmax calculated at 500 lux. conversion from  
                        # solar w/m2 to lux is 1000 w/m2 is 120,000 lux
    
def main():
        
    Irradiance = []
    time = []
    
    with open(r"C:\Users\lenovo\Desktop\Study\S9\Group_project\1_min_data.csv","r") as csvfile:
        reader = csv.DictReader(csvfile)
    
        for row in reader:
            Irradiance.append(float(row["Global Horizontal [W/m^2]"]))
            time.append(row["EST"])
    
    FullDay_Plot(Irradiance)
    
    print("Dataset available from", time[0], "to", time[-1])
    
    inp_err = 0
    
    while(not inp_err):
        inp = input('Enter the current time (tttt) of day to charge: ')
        if(inp < time[0] or inp > time[-1]):
            print("\n Time not in dataset!")
            continue
        inp_err, mins = hour_to_sec(inp)
    
    V_err = 1
    while(V_err):
        current_V = input('Enter current voltage: ')
        if(float(current_V) < 0 or float(current_V) > V_max):
            V_err = 1
            print("Incorrect voltage range!")
            continue
        
        desired_V = input('Enter desired voltage to reach: ')
        if(float(desired_V ) < V_min or float(desired_V ) > V_max):
            V_err = 1
            print("Incorrect voltage range!")
            continue        
        V_err = 0
        
    flag, V_charge_rate, cumulative_V, time_sec = Charging_Plot(Irradiance, mins, current_V, desired_V)
    
    if (not flag):
        print("\nDesired voltage not reached by EOD!")
        sys.exit()
        
    net_V = cumulative_V[:len(time_sec)]
        
    while(True):
        print("\n\nModes of operation\noff - 0, active - 1, sense - 2, radio - 3, sleep - 4")
        
        mode = input("Enter mode of operation: ")   
        if (mode == '0'):
            discharge_rate = 0
        elif (mode == '1'):
            discharge_rate = -0.000912088*2
        elif (mode == '2'):
            discharge_rate = -0.00177615*2
        elif (mode == '3'):
            discharge_rate = -0.00555411*2
        elif (mode == '4'):
            discharge_rate = -0.000133688*2
        else:
            print("\nIncorrect mode entered! ")
            continue
        duration = input("Enter time(s) of operation: ")
    
        time_sec, net_V = discharging_Plot(V_charge_rate, net_V, time_sec, discharge_rate, duration)


# Changing input data to seconds and minutes
def hour_to_sec(data):
    data_str = [int(d) for d in str(data)]
    data_hour = int(str(data_str[0])+str(data_str[1]))
    data_min = int(str(data_str[2])+str(data_str[3]))
    
    if(len(data_str) != 4 or data_min > 60 or data_hour > 24):
        print("\n Invalid time!")
        inp_err = 0
    else:
        inp_err = 1
        
    return inp_err , (data_hour*60 + data_min - 4*60 ) # since data available from 0400


def FullDay_Plot(Irradiance):

    time_min = []
    
    power = pmax * (numpy.divide(Irradiance, Gstandard))

    print(power[200])
    # Capacitor Voltage Charging Rate at Every Time Instant(Min)
    V = numpy.sqrt(2 * power * 1 / C)  # One minute intervals

    # Power Generated at Every Time Instant(Min)
    for i in range(len(V)):
        time_min.append(i)
        
    # Total Voltage Charged in a Day
    full_day_V = numpy.cumsum(V)

    # Plot for Time in Min vs Capacitor Charging Rate
    plt.plot(time_min, V)
    plt.xlabel('Time (min)')
    plt.ylabel('Capacitor Charging Rate (V/min)')
    plt.show()
    
    # Plot for Time in Min vs Total Capacitor Voltage in a Day
    plt.plot(time_min, full_day_V)
    plt.xlabel('Time (min)')
    plt.ylabel('Cumulative Capacitor Voltage (V) ')
    plt.show()


def Charging_Plot(Irradiance, mins, current_V, desired_V):

    time_sec = []
    Mins_Irradiance = Irradiance[mins:] #Calculate for remaining day

    Sec_Irradiance = []
    l_val = len(Mins_Irradiance)

    x = numpy.linspace(0, l_val-1 , num=l_val , endpoint=True)

    irrad_interp = interp1d(x, Mins_Irradiance) # interpolating minutes into seconds
    
    xnew = numpy.linspace(0, l_val-1, num= l_val*60, endpoint=True)
    Sec_Irradiance  = irrad_interp(xnew)
    
    power = pmax * (numpy.divide(Sec_Irradiance , Gstandard))
    
    # Capacitor Voltage Charging Rate
    V_charge_rate = numpy.sqrt(2 * power * 1 / C)/60

    # Total Voltage Charged during the rest of the day
    cumulative_V = float(current_V) + numpy.cumsum(V_charge_rate)
    
    for i in range(len(cumulative_V)):
        time_sec.append(i) 
            
        if (cumulative_V[i] >= float(desired_V)):
            sec = i
            flag = 1         
            total_time = str(datetime.timedelta(seconds=sec)) # convert seconds to HH:MM:SS
            
            # Plot for Time in Min vs Total Capacitor Voltage
            plt.plot(time_sec[:i], cumulative_V[:i])
            plt.xlabel('Time (s)')
            plt.ylabel('Cumulative Capacitor Voltage (V) ')
            plt.show()
            
            print('Desired voltage reached in:',total_time )
            break
        
        else:
            flag = 0

    return flag, V_charge_rate, cumulative_V, time_sec

    
def  discharging_Plot(V_charge_rate, net_V, time_sec, discharge_rate, duration):
    
    remaining_time = 0 
    count = 0
    
    #Begin plot after first full charge upto duration of mode
    for i in range(len(time_sec), len(time_sec) + int(duration)):
        count = count + 1
        time_sec.append(i)
        net_V = numpy.append(net_V, net_V[i-1] + V_charge_rate[i-1] + discharge_rate)
        if (net_V[i] >= V_max):
            net_V[i] = V_max # upper limit to V_max
        if (net_V[i] <= V_min ):
            net_V[i] = V_min  # Lower limit to V_min
            remaining_time = int(duration) - count + 1
            print("\n\nDevice has discharged fully! ")
            if (remaining_time > 0):
                net_V, time_sec = recharge(remaining_time, time_sec, net_V, V_charge_rate, discharge_rate)
                break
            
    plt.plot(time_sec, net_V)
    plt.xlabel('Time (s)')
    plt.ylabel('Cumulative Capacitor Voltage (V)')
    plt.show()
    
    return time_sec, net_V

# When device voltage lower than lower limit and task is not finished
def recharge(remaining_time, time_sec, net_V, V_charge_rate, discharge_rate):
    
    future_charging = numpy.cumsum(V_charge_rate[time_sec[-1]:time_sec[-1]+remaining_time])
    remaining_V = net_V[-1] + (remaining_time * discharge_rate * -1) - (future_charging[remaining_time-2])

    i = len(time_sec)

    while(True):
        time_sec.append(i)
        net_V = numpy.append(net_V, net_V[i-1] + V_charge_rate[i-1] + (-0.000133688) ) # Discharge slope for sleep mode
        
        if(net_V[i] >= V_max): 
            net_V[i] = V_max
            
        if(net_V[i] <= V_min):
            print(" Device voltage too low! Switching off ")
            net_V[i] = V_min
            
        if (net_V[i] >= remaining_V): # condition to break the loop. Required V is reached
            print("Remaining voltage recharged at : ", i)
            break
        i = i+1
    
    #Calculate net voltage after charging for some time
    for i in range(len(time_sec),len(time_sec) + remaining_time):
        time_sec.append(i)
        net_V = numpy.append(net_V, net_V[i-1] + V_charge_rate[i-1] + discharge_rate)
        
    return net_V, time_sec

    
if __name__ == "__main__":
    main()