#!/bin/bash

caput opc:set_period 1
caput opc:enable 1
caput logger:enable 1
caput logger:save_interval 5
caput sniffer:enable 1
caput aeth:enable 1
caput wind:enable 1
caput pom:enable 1
caput rtk:enable 1
caput hum:enable 1
caput pops:enable 1
caput rtk_arduino:enable 1
caput logger_rtk:enable 1
caput logger_rtk:save_rtk 1
caput logger_pops:enable 1
caput logger_pops:save_pops 1
caput logger_hum:enable 1
caput logger_hum:save_hum 1
caput logger_pom:enable 1
caput logger_pom:save_pom 1
caput logger_rtk_arduino:enable 1
caput logger_rtk_arduino:save_rtk 1
