# Interpolation in milliseconds - TO CONFIRM IF NEEDED
# Prediction of voltage depending on value ( say we need 2V after discharge )
# Automation of tasks to be done ( maybe with reading some csv )
# How much to sleep to finish task in one shot - DONE APPROX

# C:\Users\lenovo\Desktop\Study\S9\Group_project\Task_description.csv

import csv, sys, os
import numpy
import matplotlib.pyplot as plt
import datetime

V_max = 3.3 # Device max voltage
V_min = 1.8 # Device min voltage
C = 0.5 # Capacitance in Farad
pmax = 0.000418 # Datasheet of LH3 solar cell
Gstandard = 500/120 # pmax calculated at 500 lux. conversion from  
                        # solar w/m2 to lux is 1000 w/m2 is 120,000 lux
    
def main():
        
    #Irradiance = []
    time = []
    power_data = []
    
    with open(r"C:\Users\lenovo\Desktop\Study\S9\Group_project\capture.csv","r") as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            if(row["Date"] == "02-11-2022"):
                power_data.append(float(row["Power"]))
                time.append(row["Time"])
    
    csvfile.close()
    
    FullDay_Plot(power_data)
    
    print("Dataset available from", time[0], "to", time[-1])
    
    inp_err = 0
    
    while(not inp_err):
        inp = input('Enter the current time (hhmm/hhmmss) of day to charge: ')
        if(inp < time[0] or inp > time[-1]):
            print("\n Time not in dataset!")
            continue
        inp_err, sec = hour_to_sec(inp)
    
    file_flag = input("Task file present? (y/n) : ")
    
    while(file_flag != 'y' and file_flag != 'n'):
        print("Invalid input!")
        file_flag = input("Task file present? (y/n) : ")
    
    if(file_flag =='y'):
        
        #file_path = r"C:\Users\lenovo\Desktop\Study\S9\Group_project\Task_description.csv"
        file_path = input("Enter file path: ")
        
        if os.path.exists(file_path):
            with open(file_path,"r") as csvfile_2:
                reader = csv.DictReader(csvfile_2)
                for row in reader:
                    if(row["current_V"]==''):
                        continue
                    else:
                        current_V = row["current_V"]
                        desired_V = row["desired_V"]
            
    else:
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

    flag, V_charge_rate, cumulative_V, time_sec = Charging_Plot(power_data, sec, current_V, desired_V)
    
    if (not flag):
        print("\nDesired voltage not reached by EOD!")
        sys.exit()
        
    net_V = cumulative_V[:len(time_sec)]
    
    while(True):
        
        if(file_flag == 'y'):
            with open(file_path,"r") as csvfile_2:
                reader = csv.DictReader(csvfile_2)
                for row in reader:             
                    mode = row["mode"]
                    duration = int(row["duration"])   

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
                            
                    time_sec, net_V = discharging_Plot(V_charge_rate, net_V, time_sec, discharge_rate, duration)
                
                csvfile_2.close()
                break
            
        else:    
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
            duration = int(input("Enter time(s) of operation: "))
        
            time_sec, net_V = discharging_Plot(V_charge_rate, net_V, time_sec, discharge_rate, duration)


# Changing input data to seconds and minutes
def hour_to_sec(data):
    data_str = [int(d) for d in str(data)]
    if(len(data)==4):
        data_str.append(0)
        data_str.append(0)
    data_hour = int(str(data_str[0])+str(data_str[1]))
    data_min = int(str(data_str[2])+str(data_str[3]))
    data_sec = int(str(data_str[4])+str(data_str[5]))
    
    if(len(data_str) > 6 or data_min > 59 or data_hour > 23 or data_sec>59):
        print("\n Invalid time!")
        inp_err = 0
    else:
        inp_err = 1
        
    return inp_err , (data_hour*60*60 + data_min*60 + data_sec) # since data available from 0400


def FullDay_Plot(power_data):

    time_sec = []
    V = []
    
    #power = pmax * (numpy.divide(Irradiance, Gstandard))

    power = (numpy.divide(power_data, 1000000))

    # Capacitor Voltage Charging Rate at Every Time Instant(Min)
    for i in range(len(power)):
        V.append(numpy.sqrt(2 * float(power[i]) / (C)))  # One second intervals

    # Power Generated at Every Time Instant(Min)
    for i in range(len(V)):
        time_sec.append(i)
        
    # Total Voltage Charged in a Day
    full_day_V = numpy.cumsum(V)

    # Plot for Time in Min vs Capacitor Charging Rate
    plt.plot(time_sec, V)
    plt.xlabel('Time (sec)')
    plt.ylabel('Capacitor Charging Rate (V/s)')
    plt.show()
    
    # Plot for Time in Min vs Total Capacitor Voltage in a Day
    plt.plot(time_sec, full_day_V)
    plt.xlabel('Time (sec)')
    plt.ylabel('Cumulative Capacitor Voltage (V) ')
    plt.show()


def Charging_Plot(power_data, sec, current_V, desired_V):

    time_sec = []
    V_charge_rate = []

    power = (numpy.divide(power_data[sec:], 1000000))
    
    # Capacitor Voltage Charging Rate
    for i in range(len(power)):
        V_charge_rate.append(numpy.sqrt(2 * float(power[i]) / (C)))

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

    #Begin plot after first full charge upto duration of mode
    for i in range(len(time_sec), len(time_sec) + int(duration)):


        future_charging = numpy.cumsum(V_charge_rate[time_sec[-1]:time_sec[-1]+ duration])
        required_V = (int(duration) * discharge_rate * -1) - (future_charging[-1])
        
        if (net_V[i-1] + required_V >= V_max):
            print("Cannot reach required voltage in one shot!")
            net_V[i-1] = V_max # upper limit to V_max
        if (net_V[i-1] - required_V <= V_min):

            print("\nCurrent V :",net_V[-1])
            print("\nRequired V :",required_V)
            
            print("\n\nDevice will discharge fully! ")
            print("\nRecharging in sleep mode ... ")

            net_V, time_sec = recharge(duration, time_sec, net_V, V_charge_rate, discharge_rate, required_V)
            break
  
        time_sec.append(i) 
        net_V = numpy.append(net_V, net_V[i-1] + V_charge_rate[i-1] + discharge_rate)
        
    plt.plot(time_sec, net_V)
    plt.xlabel('Time (s)')
    plt.ylabel('Cumulative Capacitor Voltage (V)')
    plt.show()
    
    return time_sec, net_V

# When device voltage lower than lower limit and task is not finished
def recharge(duration, time_sec, net_V, V_charge_rate, discharge_rate, required_V):

    i = len(time_sec)

    while(True):
        time_sec.append(i)
        net_V = numpy.append(net_V, net_V[i-1] + V_charge_rate[i-1] + (-0.000133688) ) # Discharge slope for sleep mode
        
    #    if(net_V[i] >= V_max): 
    #        net_V[i] = V_max
    #        
    #    if(net_V[i] <= V_min):
    #        print(" Device voltage too low!")
    #        net_V[i] = V_min
            
        if (net_V[i] >= required_V + V_min + 0.01): # condition to break the loop. Required V is reached
            print("Remaining voltage recharged at : ", i)
            break
        i = i+1
    
    #Calculate net voltage after charging for some time
    for i in range(len(time_sec),len(time_sec) + duration):
        time_sec.append(i)
        net_V = numpy.append(net_V, net_V[i-1] + V_charge_rate[i-1] + discharge_rate)
        
    return net_V, time_sec

    
if __name__ == "__main__":
    main()