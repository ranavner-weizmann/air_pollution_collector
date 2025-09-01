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

class humLogger():

    def __init__(self,config_data,hum_dev_epics,logger_hum_dev_epics):

        logging.info("Instantiated humLogger class!")

        self.config_data = config_data
        self.hum_dev_epics = hum_dev_epics
        self.logger_hum_dev_epics = logger_hum_dev_epics
        self.logger_hum_dev_epics.folder_name = self.config_data['logger_hum']['save_folder']
        self.logger_hum_dev_epics.project_name = self.config_data['logger_hum']['project_name']
        self.list_hum_PVs = self.config_data['logger_hum']['hum_PVs']

        self.hum_meta=[]
        self.hum_meta.append('None') # the counts units for hum records
        for pv_name in self.list_hum_PVs:
            self.pv_type = self.hum_dev_epics.PV(pv_name).type
            if self.pv_type == 'time_double':
                self.hum_meta.append(self.hum_dev_epics.get(pv_name + '.EGU'))
            elif self.pv_type == 'time_enum':
                self.hum_meta.append("BOOL")
            else:
                self.hum_meta.append("None")

        hum_header = ['hum_' + hum_pv_name for hum_pv_name in self.list_hum_PVs]
        self.hum_df_array = pd.DataFrame(columns=hum_header)

    def update_hum_dataframe(self):

        self.hum_dict_single = dict()
        for pv_name in self.list_hum_PVs:
            self.hum_dict_single['hum_' + pv_name] = [self.hum_dev_epics.get(pv_name)]
        
        self.hum_df_single = pd.DataFrame.from_dict(self.hum_dict_single) 
        # append to array dataframe of hum data
        self.hum_df_array = self.hum_df_array.append(self.hum_df_single)#, ignore_index=True)

    def write_to_file(self):

        self.hum_mean_df = self.hum_df_array.mean().to_frame().T
        self.concat_df = pd.DataFrame({'date_time':[datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')]})
        self.concat_df.columns = pd.MultiIndex.from_tuples(zip(self.concat_df.columns, ['None']))
        self.hum_mean_df.insert(0,'hum_mean_count', [len(self.hum_df_array)])
        self.logger_hum_dev_epics.no_records_saved_hum = len(self.hum_df_array)
        self.hum_mean_df.columns = pd.MultiIndex.from_tuples(zip(self.hum_mean_df.columns, self.hum_meta))

        self.file_name_and_path = os.path.join(self.logger_hum_dev_epics.get('folder_name', as_string=True), self.logger_hum_dev_epics.get('file_name', as_string=True))

        self.concat_df = pd.concat([self.concat_df, self.hum_mean_df], axis=1, sort=False) 
        self.concat_df.to_csv(self.file_name_and_path, mode='a', header=not os.path.exists(self.file_name_and_path),index=False)

        hum_header = ['hum_' + hum_pv_name for hum_pv_name in self.list_hum_PVs]
        self.hum_df_array = pd.DataFrame(columns=hum_header)




if __name__ == "__main__":

    hum_dev_epics = epics.Device('hum:')
    logger_hum_dev_epics = epics.Device('logger_hum:')
    os.chdir('/home/pi/Documents/github/drone_dori/logger')

    with open('../config/config.yaml') as file:
        config_data = yaml.load(file, Loader=yaml.FullLoader)

    hum_logger = humLogger(config_data,hum_dev_epics,logger_hum_dev_epics)
    hum_logger.logger_hum_dev_epics.file_name = hum_logger.logger_hum_dev_epics.get('project_name', as_string=True)+datetime.datetime.now().strftime('_%Y-%m-%d_%H-%M-%S.csv')
    
    while True:   # In the future it will be while logger is on

        if logger_hum_dev_epics.enable == 1:
            hum_logger.logger_hum_dev_epics.file_name = hum_logger.logger_hum_dev_epics.get('project_name', as_string=True)+datetime.datetime.now().strftime('_%Y-%m-%d_%H-%M-%S.csv')
            while logger_hum_dev_epics.enable == 1:
                # if logger_hum_dev_epics.save_hum == 1:
    
                for i in range(num_per_average):
                    hum_logger.update_hum_dataframe()
                    logging.info('Date was updated')
                    time.sleep(1)

                hum_logger.write_to_file()
                logging.info('Data saved into file')
            else:
                logging.info('save_hum epics variable is disable')
        
        else:
            logging.info('logger_hum_dev_epics is disable')
