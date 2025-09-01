import epics
import time
import threading
from sys import exit

s = ['imu_gps_rtc:acc_direction_x', 'imu_gps_rtc:acc_direction_y', 'imu_gps_rtc:acc_direction_z', 'imu_gps_rtc:gyro_rotation_x', 'imu_gps_rtc:gyro_rotation_y', 'imu_gps_rtc:gyro_rotation_z', 'imu_gps_rtc:time', 'imu_gps_rtc:latitude', 'imu_gps_rtc:longitude', 'imu_gps_rtc:altitude', 'imu_gps_rtc:accuracy', 'hum:pressure', 'hum:temp', 'hum:rel_hum', 'hum:hum_temp', 'hum:time', 'hum:longitude', 'hum:latitude', 'hum:altitude', 'hum:sat', 'aeth:comm_ON', 'aeth:tape_at_end_ON', 'aeth:sampling_ON', 'aeth:enable', 'aeth:data_ready', 'aeth:datum_id', 'aeth:session_id', 'aeth:data_format_ver', 'aeth:firmware_version', 'aeth:date_time_GMT', 'aeth:timezone_offset', 'aeth:gps_lat', 'aeth:gps_long', 'aeth:gps_speed', 'aeth:timebase', 'aeth:status', 'aeth:battery', 'aeth:accel_x', 'aeth:accel_y', 'aeth:accel_z', 'aeth:tape_pos', 'aeth:flow_setpoint', 'aeth:flow_total', 'aeth:flow1', 'aeth:flow2', 'aeth:sample_temp', 'aeth:sample_RH', 'aeth:sample_dewpoint', 'aeth:int_pressure', 'aeth:int_temp', 'aeth:optical_config', 'aeth:UV_sen1', 'aeth:UV_sen2', 'aeth:UV_ref', 'aeth:UV_ATN1', 'aeth:UV_ATN2', 'aeth:UV_K', 'aeth:blue_sen1', 'aeth:blue_sen2', 'aeth:blue_ref', 'aeth:blue_ATN1', 'aeth:blue_ATN2', 'aeth:blue_K', 'aeth:green_sen1', 'aeth:green_sen2', 'aeth:green_ref', 'aeth:green_ATN1', 'aeth:green_ATN2', 'aeth:green_K', 'aeth:red_sen1', 'aeth:red_sen2', 'aeth:red_ref', 'aeth:red_ATN1', 'aeth:red_ATN2', 'aeth:red_K', 'aeth:IR_sen1', 'aeth:IR_sen2', 'aeth:IR_ref', 'aeth:IR_ATN1', 'aeth:IR_ATN2', 'aeth:IR_K', 'aeth:UV_BC1', 'aeth:UV_BC2', 'aeth:UV_BCc', 'aeth:blue_BC1', 'aeth:blue_BC2', 'aeth:blue_BCc', 'aeth:green_BC1', 'aeth:green_BC2', 'aeth:green_BCc', 'aeth:red_BC1', 'aeth:red_BC2', 'aeth:red_BCc', 'aeth:IR_BC1', 'aeth:IR_BC2', 'aeth:IR_BCc', 'opc:period', 'opc:Flowrate', 'opc:pm1', 'opc:pm2dot5', 'opc:pm10', 'opc:bins', 'opc:laser_status', 'pops:enable', 'pops:DateTime', 'pops:TimeSSM', 'pops:Status', 'pops:DataStatus', 'pops:PartCt', 'pops:HistSum', 'pops:PartCon', 'pops:BL', 'pops:BLTH', 'pops:STD', 'pops:MaxSTD', 'pops:P', 'pops:TofP', 'pops:PumpLife_hrs', 'pops:WidthSTD', 'pops:AveWidth', 'pops:POPS_Flow', 'pops:Pump_FB', 'pops:LDTemp', 'pops:LaserFB', 'pops:LD_Mon', 'pops:Temp', 'pops:BatV', 'pops:LD_Mon', 'pops:Flow_Set', 'pops:BL_Start', 'pops:TH_Mult', 'pops:nbins', 'pops:logmin', 'pops:logmax', 'pops:Skip_save', 'pops:MinPeakPts', 'pops:MaxPeakPts', 'pops:RawPts', 'pops:b0', 'pops:b1', 'pops:b2', 'pops:b3', 'pops:b4', 'pops:b5', 'pops:b6', 'pops:b7', 'pops:b8', 'pops:b9', 'pops:b10', 'pops:b11', 'pops:b12', 'pops:b13', 'pops:b14', 'pops:b15', 'pops:bins', 'pom:ozone', 'pom:cell_temp', 'pom:cell_pressure', 'pom:photo_volt', 'pom:power_supply', 'pom:latitude', 'pom:longitude', 'pom:altitude']


def thread_function(id, pvs : list):
    while True:
        t = time.time()
        # print([pv.get() for pv in pvs])
        # print(f"{id} Took: {time.time() - t} seconds.")
        return time.time() - t


pvs = [epics.PV(pv) for pv in s]

# x = threading.Thread(target=thread_function, args=(1, pvs[:82]))
# y = threading.Thread(target=thread_function, args=(2, pvs[82: ]))

# x.start()
# y.start()
max_index = 0
max_time = 0

for i in range(165):
    t = thread_function(i, pvs[:i])
    if (t > max_time):
        max_index = i
        max_time = t

print(max_index, max_time)

# t = time.time()
# print(pvs[162].get())
# print(pvs[162])
# print(time.time() - t)





