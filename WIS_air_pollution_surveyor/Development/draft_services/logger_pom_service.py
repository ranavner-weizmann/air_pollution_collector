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

class PomLogger():

    def __init__(self,config_data,pom_dev_epics,logger_pom_dev_epics):

        # pom initialization
        logging.info("Instantiated PomLogger class!")

        self.config_data = config_data
        self.pom_dev_epics = pom_dev_epics
        self.logger_pom_dev_epics = logger_pom_dev_epics
        self.logger_pom_dev_epics.folder_name = self.config_data['logger_pom']['save_folder']
        self.logger_pom_dev_epics.project_name = self.config_data['logger_pom']['project_name']
        self.list_pom_PVs = self.config_data['logger_pom']['pom_PVs']

        # Header creator

        self.pom_meta=[]
        self.pom_meta.append('None') # the counts units for pom records
        for pv_name in self.list_pom_PVs:
            self.pv_type = self.pom_dev_epics.PV(pv_name).type
            if self.pv_type == 'time_double':
                self.pom_meta.append(self.pom_dev_epics.get(pv_name + '.EGU'))
                # opc_device.PV('pm1').get_ctrlvars()  to get units in another method
            elif self.pv_type == 'time_enum':
                self.pom_meta.append("BOOL")
            else:
                self.pom_meta.append("None")

        pom_header = ['pom_' + pom_pv_name for pom_pv_name in self.list_pom_PVs]
        self.pom_df_array = pd.DataFrame(columns=pom_header)

    def update_pom_dataframe(self):

        self.pom_dict_single = dict()
        for pv_name in self.list_pom_PVs:
            self.pom_dict_single['pom_' + pv_name] = [self.pom_dev_epics.get(pv_name)]
        
        self.pom_df_single = pd.DataFrame.from_dict(self.pom_dict_single) 
        self.pom_df_array = self.pom_df_array.append(self.pom_df_single)#, ignore_index=True)

    def write_to_file(self):

        self.pom_mean_df = self.pom_df_array.mean().to_frame().T
        self.concat_df = pd.DataFrame({'date_time':[datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')]})
        self.concat_df.columns = pd.MultiIndex.from_tuples(zip(self.concat_df.columns, ['None']))
        self.pom_mean_df.insert(0,'pom_mean_count', [len(self.pom_df_array)])
        self.logger_pom_dev_epics.no_records_saved_pom = len(self.pom_df_array)
        self.pom_mean_df.columns = pd.MultiIndex.from_tuples(zip(self.pom_mean_df.columns, self.pom_meta))

        self.file_name_and_path = os.path.join(self.logger_pom_dev_epics.get('folder_name', as_string=True), self.logger_pom_dev_epics.get('file_name', as_string=True))

        self.concat_df = pd.concat([self.concat_df, self.pom_mean_df], axis=1, sort=False) 
        self.concat_df.to_csv(self.file_name_and_path, mode='a', header=not os.path.exists(self.file_name_and_path),index=False)

        pom_header = ['pom_' + pom_pv_name for pom_pv_name in self.list_pom_PVs]
        self.pom_df_array = pd.DataFrame(columns=pom_header)

if __name__ == "__main__":

    pom_dev_epics = epics.Device('pom:')
    logger_pom_dev_epics = epics.Device('logger_pom:')
    os.chdir('/home/pi/Documents/github/drone_dori/logger')

    with open('../config/config.yaml') as file:
        config_data = yaml.load(file, Loader=yaml.FullLoader)

    pom_logger = PomLogger(config_data,pom_dev_epics,logger_pom_dev_epics)
    pom_logger.logger_pom_dev_epics.file_name = pom_logger.logger_pom_dev_epics.get('project_name', as_string=True)+datetime.datetime.now().strftime('_%Y-%m-%d_%H-%M-%S.csv')
    
    while True:   

        if logger_pom_dev_epics.enable == 1:
            pom_logger.logger_pom_dev_epics.file_name = pom_logger.logger_pom_dev_epics.get('project_name', as_string=True)+datetime.datetime.now().strftime('_%Y-%m-%d_%H-%M-%S.csv')
            while logger_pom_dev_epics.enable == 1:
                if logger_pom_dev_epics.save_pom == 1:
                    pom_logger.update_pom_dataframe()
                    logging.info('Date was updated')
                    pom_logger.write_to_file()
                    logging.info('Data saved into file')
                    time.sleep(0.5)
                else:
                    logging.info('save_pom epics variable is disable')
        
        else:
            logging.info('logger_pom_dev_epics is disable')