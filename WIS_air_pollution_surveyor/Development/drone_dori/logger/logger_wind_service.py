 #What is the structure that I want to build here? 
#I get have access to epics varialbes: speed, direction and temperature. 

import epics
import yaml
import pandas as pd
import os
import time
import logging
import datetime

num_per_average = 3

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

class WindLogger():

    def __init__(self,config_data,wind_dev_epics,logger_wind_dev_epics):

        # Wind initialization
        logging.info("Instantiated WindLogger class!")

        self.config_data = config_data
        self.wind_dev_epics = wind_dev_epics
        self.logger_wind_dev_epics = logger_wind_dev_epics
        self.logger_wind_dev_epics.folder_name = self.config_data['logger_wind']['save_folder']
        self.logger_wind_dev_epics.project_name = self.config_data['logger_wind']['project_name']
        self.list_wind_PVs = self.config_data['logger_wind']['wind_PVs']

        # Header creator

        self.wind_meta=[]
        self.wind_meta.append('None') # the counts units for wind records
        for pv_name in self.list_wind_PVs:
            self.pv_type = self.wind_dev_epics.PV(pv_name).type
            if self.pv_type == 'time_double':
                self.wind_meta.append(self.wind_dev_epics.get(pv_name + '.EGU'))
                # opc_device.PV('pm1').get_ctrlvars()  to get units in another method
            elif self.pv_type == 'time_enum':
                self.wind_meta.append("BOOL")
            else:
                self.wind_meta.append("None")

        wind_header = ['wind_' + wind_pv_name for wind_pv_name in self.list_wind_PVs]
        self.wind_df_array = pd.DataFrame(columns=wind_header)

    def update_wind_dataframe(self):

        self.wind_dict_single = dict()
        for pv_name in self.list_wind_PVs:
            self.wind_dict_single['wind_' + pv_name] = [self.wind_dev_epics.get(pv_name)]
        
        self.wind_df_single = pd.DataFrame.from_dict(self.wind_dict_single) 
        # append to array dataframe of wind data
        self.wind_df_array = self.wind_df_array.append(self.wind_df_single)#, ignore_index=True)

    def write_to_file(self):

        self.wind_mean_df = self.wind_df_array.mean().to_frame().T
        self.concat_df = pd.DataFrame({'date_time':[datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')]})
        self.concat_df.columns = pd.MultiIndex.from_tuples(zip(self.concat_df.columns, ['None']))
        self.wind_mean_df.insert(0,'wind_mean_count', [len(self.wind_df_array)])
        self.logger_wind_dev_epics.no_records_saved_wind = len(self.wind_df_array)
        self.wind_mean_df.columns = pd.MultiIndex.from_tuples(zip(self.wind_mean_df.columns, self.wind_meta))

        self.file_name_and_path = os.path.join(self.logger_wind_dev_epics.get('folder_name', as_string=True), self.logger_wind_dev_epics.get('file_name', as_string=True))

        self.concat_df = pd.concat([self.concat_df, self.wind_mean_df], axis=1, sort=False) 
        self.concat_df.to_csv(self.file_name_and_path, mode='a', header=not os.path.exists(self.file_name_and_path),index=False)

        wind_header = ['wind_' + wind_pv_name for wind_pv_name in self.list_wind_PVs]
        self.wind_df_array = pd.DataFrame(columns=wind_header)

                



if __name__ == "__main__":

    wind_dev_epics = epics.Device('wind:')
    logger_wind_dev_epics = epics.Device('logger_wind:')
    os.chdir('/home/pi/Documents/github/drone_dori/logger')

    with open('../config/config.yaml') as file:
        config_data = yaml.load(file, Loader=yaml.FullLoader)

    wind_logger = WindLogger(config_data,wind_dev_epics,logger_wind_dev_epics)
    wind_logger.logger_wind_dev_epics.file_name = wind_logger.logger_wind_dev_epics.get('project_name', as_string=True)+datetime.datetime.now().strftime('_%Y-%m-%d_%H-%M-%S.csv')
    
    while True:   # In the future it will be while logger is on

        if logger_wind_dev_epics.enable == 1:
            wind_logger.logger_wind_dev_epics.file_name = wind_logger.logger_wind_dev_epics.get('project_name', as_string=True)+datetime.datetime.now().strftime('_%Y-%m-%d_%H-%M-%S.csv')
            while logger_wind_dev_epics.enable == 1:
                if logger_wind_dev_epics.save_wind == 1:
    
                    for i in range(num_per_average):
                        wind_logger.update_wind_dataframe()
                        logging.info('Date was updated')
                        time.sleep(1)

                    wind_logger.write_to_file()
                    logging.info('Data saved into file')
                else:
                    logging.info('save_wind epics variable is disable')
        
        else:
            logging.info('logger_wind_dev_epics is disable')

# print('hello world')