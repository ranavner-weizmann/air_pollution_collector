import epics
import yaml
import pandas as pd
import os
import time
import logging
import datetime

# num_per_average = 3   
# Here, we probably don't need to average. the results are already averaged.

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

class rtkLogger():

    def __init__(self,config_data,rtk_dev_epics,logger_rtk_dev_epics):

        # rtk initialization
        logging.info("Instantiated rtkLogger class!")

        self.config_data = config_data
        self.rtk_dev_epics = rtk_dev_epics
        self.logger_rtk_dev_epics = logger_rtk_dev_epics
        self.logger_rtk_dev_epics.folder_name = self.config_data['logger_rtk']['save_folder']
        self.logger_rtk_dev_epics.project_name = self.config_data['logger_rtk']['project_name']
        self.list_rtk_PVs = self.config_data['logger_rtk']['rtk_PVs']

        # Header creator

        self.rtk_meta=[]
        self.rtk_meta.append('None') # the counts units for rtk records
        for pv_name in self.list_rtk_PVs:
            self.pv_type = self.rtk_dev_epics.PV(pv_name).type
            if self.pv_type == 'time_double':
                self.rtk_meta.append(self.rtk_dev_epics.get(pv_name + '.EGU'))
                # opc_device.PV('pm1').get_ctrlvars()  to get units in another method
            elif self.pv_type == 'time_enum':
                self.rtk_meta.append("BOOL")
            else:
                self.rtk_meta.append("None")

        rtk_header = ['rtk_' + rtk_pv_name for rtk_pv_name in self.list_rtk_PVs]
        self.rtk_df_array = pd.DataFrame(columns=rtk_header)
        # print('just for debug')

    def update_rtk_dataframe(self):

        self.rtk_dict_single = dict()
        for pv_name in self.list_rtk_PVs:
            self.rtk_dict_single['rtk_' + pv_name] = [self.rtk_dev_epics.get(pv_name)]
        
        self.rtk_df_single = pd.DataFrame.from_dict(self.rtk_dict_single) 
        # append to array dataframe of rtk data
        self.rtk_df_array = self.rtk_df_array.append(self.rtk_df_single)#, ignore_index=True)

    def write_to_file(self):

        self.rtk_mean_df = self.rtk_df_array.mean().to_frame().T
        self.concat_df = pd.DataFrame({'date_time':[datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')]})
        self.concat_df.columns = pd.MultiIndex.from_tuples(zip(self.concat_df.columns, ['None']))
        self.rtk_mean_df.insert(0,'rtk_mean_count', [len(self.rtk_df_array)])
        self.logger_rtk_dev_epics.no_records_saved_rtk = len(self.rtk_df_array)
        self.rtk_mean_df.columns = pd.MultiIndex.from_tuples(zip(self.rtk_mean_df.columns, self.rtk_meta))

        self.file_name_and_path = os.path.join(self.logger_rtk_dev_epics.get('folder_name', as_string=True), self.logger_rtk_dev_epics.get('file_name', as_string=True))

        self.concat_df = pd.concat([self.concat_df, self.rtk_mean_df], axis=1, sort=False) 
        self.concat_df.to_csv(self.file_name_and_path, mode='a', header=not os.path.exists(self.file_name_and_path),index=False)

        rtk_header = ['rtk_' + rtk_pv_name for rtk_pv_name in self.list_rtk_PVs]
        self.rtk_df_array = pd.DataFrame(columns=rtk_header)

if __name__ == "__main__":

    rtk_dev_epics = epics.Device('rtk:')
    logger_rtk_dev_epics = epics.Device('logger_rtk:')
    os.chdir('/home/pi/Documents/github/drone_dori/logger')

    with open('../config/config.yaml') as file:
        config_data = yaml.load(file, Loader=yaml.FullLoader)

    rtk_logger = rtkLogger(config_data,rtk_dev_epics,logger_rtk_dev_epics)
    rtk_logger.logger_rtk_dev_epics.file_name = rtk_logger.logger_rtk_dev_epics.get('project_name', as_string=True)+datetime.datetime.now().strftime('_%Y-%m-%d_%H-%M-%S.csv')
    
    while True:   # In the future it will be while logger is on
        if logger_rtk_dev_epics.enable == 1:
            rtk_logger.logger_rtk_dev_epics.file_name = rtk_logger.logger_rtk_dev_epics.get('project_name', as_string=True)+datetime.datetime.now().strftime('_%Y-%m-%d_%H-%M-%S.csv')         
            while logger_rtk_dev_epics.enable == 1:
                # if logger_rtk_dev_epics.save_rtk == 1:
                rtk_logger.update_rtk_dataframe()
                logging.info('Date was updated')
                rtk_logger.write_to_file()
                logging.info('Data saved into file')
                time.sleep(1)
                # else:
                #     logging.info('save_rtk epics variable is disable')
        
        else:
            logging.info('logger_rtk_dev_epics is disable')