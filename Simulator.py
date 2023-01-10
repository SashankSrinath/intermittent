import csv, sys, os, numpy, datetime
import matplotlib.pyplot as plt

V_max = 3.3 # Device max voltage
V_min = 1.8 # Device min voltage
C = 0.5 # Capacitance in Farad
pmax = 0.000418 # Datasheet of LH3 solar cell. NOTE: Not used anymore
Gstandard = 500/120 # pmax calculated at 500 lux. conversion from  
                        # solar w/m2 to lux is 1000 w/m2 is 120,000 lux
                        #  Not used in current version
    
def main():
        
    time = []
    power_data = []
    accuracy = []
    
    current_V = 0
    desired_V = 0
    
    
    # Reading the dataset
    with open(r"C:\Users\lenovo\Desktop\Study\S9\Group_project\capture.csv","r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if(row["Date"] == "02-11-2022"):
                power_data.append(float(row["Power"]))
                time.append(row["Time"])   
    csvfile.close()
    
    # Plot for the capacitor charging rate vs time and cumulative V vs time
    fullDay_Plot(power_data)
    
    #performance_analysis(power_data)
    
    with open('Accuracy.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            accuracy.append(row['Relative error'])
    
    print("\nDataset available from", time[0], "to", time[-1])
    
    inp_err = 0
    
    while(not inp_err):
        inp = input('Enter the current time (hhmm/hhmmss) of day to charge: ')
        if(inp < time[0] or inp > time[-1]):
            print("\n Time not in dataset!")
            continue
        inp_err, sec = hour_to_sec(inp)
    
    # Check if user wants to give task description file or not
    file_flag = input("Task description file present? (y/n) : ")
    
    while(file_flag != 'y' and file_flag != 'n'):
        print("Invalid input!")
        file_flag = input("Task file present? (y/n) : ")
    
    if(file_flag =='y'):
        
        file_path = r"C:\Users\lenovo\Desktop\Study\S9\Group_project\Task_description.csv"
        #file_path = input("Enter file path: ")
        
        # Get current_V and desired_V from file
        if os.path.exists(file_path):
            with open(file_path,"r") as csvfile_2:
                reader = csv.DictReader(csvfile_2)
                for row in reader:
                    if(row["current_V"]==''):
                        continue
                    else:
                        current_V = row["current_V"]
                        desired_V = row["desired_V"]     
    # Get from user if no file is given                     
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
    
   
    # Plot the initial charging plot from current_V to desired_V
    flag, V_charge_rate, cumulative_V, time_sec = initial_charging(power_data, sec, current_V, desired_V)
    
    if (not flag):
        print("\nDesired voltage not reached by EOD!")
        sys.exit()
        
    net_V = cumulative_V[:len(time_sec)]
    
    while(True):
        
        # Read the modes and duration from the description file
        if(file_flag == 'y'):
            with open(file_path,"r") as csvfile_2:
                reader = csv.DictReader(csvfile_2)
                for row in reader:             
                    mode = int(row["mode"])
                    duration = int(row["duration"])
                    discharge_rate = set_discharge(mode)
                    
                    if(mode != 4):
                        time_sec, net_V = discharge_device(V_charge_rate, net_V, time_sec, discharge_rate, duration)
                    
                    else:
                        target_V = float(row["target_V"])
                        time_sec, net_V = sleep_mode(V_charge_rate, net_V, time_sec, discharge_rate,target_V,sec,accuracy)
                    
                csvfile_2.close()
                break
            
        else:    
            print("\n\nModes of operation\noff - 0, active - 1, sense - 2, radio - 3, sleep - 4")
            mode = int(input("Enter mode of operation: "))
            discharge_rate = set_discharge(mode)
            
            if(mode != 4):
                duration = int(input("Enter time(s) of operation: "))
                time_sec, net_V = discharge_device(V_charge_rate, net_V, time_sec, discharge_rate, duration)
            
            else:
                V_err = 1
                while(V_err):
                    target_V = input("Enter desired voltage to reach: ")
                    if(float(target_V  ) < net_V[-1] or float(target_V  ) > V_max):
                        V_err = 1
                        print("Incorrect voltage range!")
                        continue        
                    V_err = 0
                time_sec, net_V = sleep_mode(V_charge_rate, net_V, time_sec, discharge_rate,target_V,sec,accuracy)
              

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


def fullDay_Plot(power_data):

    time_sec = []
    V = []
    
    power = (numpy.divide(power_data, 1000000))

    # Capacitor Voltage Charging Rate at Every Time Instant
    for i in range(len(power)):
        V.append(numpy.sqrt(2 * float(power[i]) / (C)))  # One second intervals

    # Power Generated at Every Time Instant
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


def initial_charging(power_data, sec, current_V, desired_V):

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

    
def set_discharge(mode):                      
    if (mode == 0):
        discharge_rate = 0
    elif (mode == 1):
        discharge_rate = -0.000912088*2
        
    elif (mode == 2):
        discharge_rate = -0.00177615*2
        
    elif (mode == 3):
        discharge_rate = -0.00555411*2
        
    elif (mode == 4):
        discharge_rate = -0.000133688*2
    
    return discharge_rate

                        
def discharge_device(V_charge_rate, net_V, time_sec, discharge_rate, duration):

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

            net_V, time_sec = recharge_device(duration, time_sec, net_V, V_charge_rate, discharge_rate, required_V)
            break
  
        time_sec.append(i) 
        net_V = numpy.append(net_V, net_V[i-1] + V_charge_rate[i-1] + discharge_rate)
        
    plt.plot(time_sec, net_V)
    plt.xlabel('Time (s)')
    plt.ylabel('Cumulative Capacitor Voltage (V)')
    plt.show()
    
    return time_sec, net_V

# When device voltage lower than lower limit and task is not finished
def recharge_device(duration, time_sec, net_V, V_charge_rate, discharge_rate, required_V):

    i = len(time_sec)

    while(True):
        time_sec.append(i)
        net_V = numpy.append(net_V, net_V[i-1] + V_charge_rate[i-1] + (-0.000133688) ) # Discharge slope for sleep mode

        if (net_V[i] >= required_V + V_min + 0.01): # condition to break the loop. Required V is reached
            print("Remaining voltage recharged at : ", i)
            break
        i = i+1
    
    #Calculate net voltage after charging for some time
    for i in range(len(time_sec),len(time_sec) + duration):
        time_sec.append(i)
        net_V = numpy.append(net_V, net_V[i-1] + V_charge_rate[i-1] + discharge_rate)
        
    return net_V, time_sec

def sleep_mode(V_charge_rate, net_V, time_sec, discharge_rate,target_V,sec,accuracy):
    
    const_time = []
    const_net_V = []
    
    pred_time = []
    pred_net_V = []
    
    actual_time = []
    actual_net_V = []
    
    desired_V = target_V
    
    constant_V_rate = float(V_charge_rate[time_sec[-1]])
    const_duration = (float(desired_V) - net_V[-1])/(constant_V_rate + discharge_rate)
    net_V_temp = net_V

    V_diff = float(desired_V) - float(net_V[-1])
    
    for i in range(len(time_sec), len(time_sec) + int(const_duration +1)):

        const_time.append(i)
        net_V_temp = numpy.append(net_V_temp, net_V_temp[i-1] + constant_V_rate + discharge_rate)
        const_net_V.append(net_V_temp[i])
        
    
    #Predicting the voltage using past 1 min charging rate
    
    # Getting the accuracy of the time instant, the user has specified 
    current_accuracy = accuracy[sec + time_sec[-1]]
    print("\nCurrent relative error from performance analysis: ",current_accuracy)
    
    weight = (float(current_accuracy)/100000) * (V_diff / 0.5) # analysis was done for 0.5V

    slope = numpy.polyfit(time_sec[-60 :],V_charge_rate[time_sec[-1]-60:time_sec[-1]], 1)
    
    slope[0] = slope[0] + weight
    
    i = len(time_sec)
    net_V_temp = net_V

    while(net_V_temp[-1] < float(desired_V)):
        pred_time.append(i)
        net_V_temp = numpy.append(net_V_temp, net_V_temp[i-1] + slope[0]*pred_time[-1] + slope[1] + discharge_rate)
        
        pred_net_V.append(net_V_temp[i])
        i+=1
        
        
    print("Time to reach desired V with 1 min slope data: ", int(pred_time[-1])-len(time_sec),'s')
    
    #Predicting the voltage with the actual data
    future_V_rate = V_charge_rate[time_sec[-1]:]
    
    j = len(time_sec)
    
    net_V_temp = net_V
    
    while(net_V_temp[-1] < float(desired_V)):
        actual_time.append(j)
        net_V_temp = numpy.append(net_V_temp, net_V_temp[j-1] + future_V_rate[j-(len(time_sec))] + discharge_rate)
        actual_net_V.append(net_V_temp[j])
        j+=1
       
    print("Time to reach desired V at actual charging rate: ", int(actual_time[-1])-len(time_sec),'s')
    
    plt.plot(time_sec, net_V)
    plt.plot(const_time,const_net_V,color ='b', linestyle = 'dashed', label = "Constant rate")
    plt.plot(pred_time,pred_net_V,color ='r', linestyle = 'dashed',  label = ("1 minute slope prediction"))
    plt.plot(actual_time,actual_net_V,color ='g', linestyle = 'dashed',  label = ("Actual rate"))
    plt.legend()
    plt.xlabel('Time (s)')
    plt.ylabel('Cumulative Capacitor Voltage (V)')
    plt.show()
    
    print("Time to reach desired V at constant charging rate: ", int(const_duration +1),'s')

    for i in range(len(pred_time)):
        time_sec.append(pred_time[i])
    net_V = numpy.append(net_V,pred_net_V)

    if(len(pred_time) < len(actual_time)):
        index = len(pred_time)-1
    else:
        index = len(actual_time)-1
    
    print("Predicted voltage at t =",index ," is : ", pred_net_V[index])
    print("Actual voltage at t =",index ," is : ", actual_net_V[index])
    print("Voltage difference: ", float(pred_net_V[index]) - float(actual_net_V[index]))
    
    return time_sec, net_V

def performance_analysis(power_data):
    
    print("Running performance analysis function ...")
    
    time_sec = []
    V_charge_rate = []
    
    accuracy = []
    final_accuracy = []
    
    relative_err = []
    final_rel = []
    
    actual_time_writer = []
    pred_time_writer = []
    
    start = 30000 # data point to start analysis
    end = 60000 # to end analysis
    discharge_rate = -0.000133688*2 # sleep mode discharge
    step = 1 # 1 second interval
    
    power = (numpy.divide(power_data, 1000000))

    # Capacitor Voltage Charging Rate at Every Time Instant
    for i in range(len(power)):
        V_charge_rate.append(numpy.sqrt(2 * float(power[i]) / (C)))  # One second intervals
        
    # Power Generated at Every Time Instant
    for i in range(len(V_charge_rate)):
        time_sec.append(i) 
   
    #for i in range(start, start+10):
    for i in range(start, end, step): # iterating for every 60 seconds from start to end
        
        pred_time = []
        pred_net_V = []
        
        actual_time = []
        actual_net_V = []
    
        #Predicting the voltage using past 1 min charging rate
        slope = numpy.polyfit(time_sec[i-60:i],V_charge_rate[i-60:i], 1)
       
        net_V = [0]
        j = i

        while(net_V[-1] <= 0.5):

            pred_time.append(j) 
            net_V = numpy.append(net_V, net_V[-1] + slope[0]*pred_time[-1] + slope[1] + discharge_rate)
            if(net_V[-1]<=0):
                net_V [-1] = 0
            pred_net_V.append(net_V[-1])
            j+=1
            if(j-i>1800): #if device doesnt charge in over 30 mins with past minute data
                print("Can't predict with past minute data at point:",i)
                break
        
        #Predicting the voltage with the actual data
        future_V_rate = V_charge_rate[time_sec[i]:]
        j = 0
        net_V = [0]

        while(net_V[-1] <= 0.5):
            actual_time.append(j)
            net_V = numpy.append(net_V, net_V[-1] + future_V_rate[j] + discharge_rate)
            if(net_V[-1]<=0):
                net_V [-1] = 0
            actual_net_V.append(net_V[j])
            j+=1

        pred_time_writer.append(int(pred_time[-1]-i))         
        actual_time_writer.append(int(actual_time[-1]))
        
        accuracy.append(int(pred_time[-1]-i) - int(actual_time[-1]))
        relative_err.append((float(pred_time[-1]-i) - float(actual_time[-1]) )/actual_time[-1])
    
    print("Performance analysis finished!")

# Replace the unpredicted elements with zero    
    for i in range(len(accuracy)):
        if accuracy[i] > 1500:
            accuracy[i] = 0
            relative_err[i] = 0
            pred_time_writer[i]  = 0
            actual_time_writer[i]  = 0
    
    # Intialize final_accuracy array with zeros        
    final_accuracy = numpy.zeros(len(time_sec), dtype=float)
    final_rel = numpy.zeros(len(time_sec), dtype=float)
    final_pred = numpy.zeros(len(time_sec), dtype=int)
    final_actual = numpy.zeros(len(time_sec), dtype=int)
    
    start_ = start
    
    # Append the calculated values to the final_accuracy array in the correct position
    for element in actual_time_writer:
        for i in range(step):
            final_actual[start + i] = element
        start += step
    
    start = start_
    for element2 in pred_time_writer:
        for i in range(step):
            final_pred[start + i] = element2
        start += step   
    
    start = start_
    for element3 in accuracy:
        for i in range(step):
            final_accuracy[start + i] = element3
        start += step
    
    start = start_
    for element4 in relative_err:
        for i in range(step):
            final_rel[start + i] = element4
        start += step
        
    with open('accuracy.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Actual time(s)', 'Predicted time(s)', 'Absolute error(s)', 'Relative error'])
        for i in range(len(final_actual)):
            writer.writerow([final_actual[i],final_pred[i], final_accuracy[i], final_rel[i]] )
            
            
if __name__ == "__main__":
    main()