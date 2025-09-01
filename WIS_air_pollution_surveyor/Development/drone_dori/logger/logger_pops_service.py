import epics
import yaml
import pandas as pd
import os
import time
import logging
import datetime
import time

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

class PopsLogger():

    def __init__(self,config_data,pops_dev_epics,logger_pops_dev_epics):

        logging.info("Instantiated humLogger class!")

        self.config_data = config_data
        self.pops_dev_epics = pops_dev_epics
        self.logger_pops_dev_epics = logger_pops_dev_epics
        self.logger_pops_dev_epics.folder_name = self.config_data['logger_pops']['save_folder']
        self.logger_pops_dev_epics.project_name = self.config_data['logger_pops']['project_name']
        self.list_pops_PVs = self.config_data['logger_pops']['pops_PVs']
        self.temp_save_interval = self.config_data['logger_pops']['interval_between_save_s']
        self.logger_pops_dev_epics.save_interval = self.temp_save_interval

        self.pops_meta=[]
        self.pops_meta.append('None') # the counts units for hum records
        for pv_name in self.list_pops_PVs:
            self.pv_type = self.pops_dev_epics.PV(pv_name).type
            if self.pv_type == 'time_double':
                self.pops_meta.append(self.pops_dev_epics.get(pv_name + '.EGU'))
            elif self.pv_type == 'time_enum':
                self.pops_meta.append("BOOL")
            else:
                self.pops_meta.append("None")

        pops_header = ['pops_' + pops_pv_name for pops_pv_name in self.list_pops_PVs]
        self.pops_df_array = pd.DataFrame(columns=pops_header)

    def update_pops_dataframe(self):

        time_stop = datetime.datetime.now() + datetime.timedelta(seconds=self.temp_save_interval)
        while datetime.datetime.now() < time_stop:

            self.pops_dict_single = dict()
            for pv_name in self.list_pops_PVs:
                self.pops_dict_single['pops_' + pv_name] = [self.pops_dev_epics.get(pv_name)]
            
            self.pops_df_single = pd.DataFrame.from_dict(self.pops_dict_single) 
            # append to array dataframe of pops data
            self.pops_df_array = self.pops_df_array.append(self.pops_df_single)#, ignore_index=True)

        self.pops_df_array.drop_duplicates(inplace=True)

    def write_to_file(self):

        self.pops_mean_df = self.pops_df_array.mean().to_frame().T
        self.concat_df = pd.DataFrame({'date_time':[datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')]})
        self.concat_df.columns = pd.MultiIndex.from_tuples(zip(self.concat_df.columns, ['None']))
        self.pops_mean_df.insert(0,'pops_mean_count', [len(self.pops_df_array)])
        self.logger_pops_dev_epics.no_records_saved_pops = len(self.pops_df_array)
        self.pops_mean_df.columns = pd.MultiIndex.from_tuples(zip(self.pops_mean_df.columns, self.pops_meta))

        self.file_name_and_path = os.path.join(self.logger_pops_dev_epics.get('folder_name', as_string=True), self.logger_pops_dev_epics.get('file_name', as_string=True))

        self.concat_df = pd.concat([self.concat_df, self.pops_mean_df], axis=1, sort=False) 
        self.concat_df.to_csv(self.file_name_and_path, mode='a', header=not os.path.exists(self.file_name_and_path),index=False)

        pops_header = ['pops_' + pops_pv_name for pops_pv_name in self.list_pops_PVs]
        self.pops_df_array = pd.DataFrame(columns=pops_header)


if __name__ == "__main__":

    pops_dev_epics = epics.Device('pops:')
    logger_pops_dev_epics = epics.Device('logger_pops:')
    os.chdir('/home/pi/Documents/github/drone_dori/logger')

    with open('../config/config.yaml') as file:
        config_data = yaml.load(file, Loader=yaml.FullLoader)

    pops_logger = PopsLogger(config_data,pops_dev_epics,logger_pops_dev_epics)
    pops_logger.logger_pops_dev_epics.file_name = pops_logger.logger_pops_dev_epics.get('project_name', as_string=True)+datetime.datetime.now().strftime('_%Y-%m-%d_%H-%M-%S.csv')

    while True:   
        if logger_pops_dev_epics.enable == 1:
            pops_logger.logger_pops_dev_epics.file_name = pops_logger.logger_pops_dev_epics.get('project_name', as_string=True)+datetime.datetime.now().strftime('_%Y-%m-%d_%H-%M-%S.csv')
            while logger_pops_dev_epics.enable == 1:
                if logger_pops_dev_epics.save_pops == 1:
                    pops_logger.update_pops_dataframe()
                    logging.info('Date was updated')
                    pops_logger.write_to_file()
                    logging.info('Data saved into file')
                    time.sleep(0.5)
                else:
                    logging.info('save_pops epics variable is disable')
        
        else:
            logging.info('logger_pops_dev_epics is disable')