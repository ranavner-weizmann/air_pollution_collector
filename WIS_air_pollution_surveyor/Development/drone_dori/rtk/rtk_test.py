# from email import parser
import serial
from ublox_gps import UbloxGps
# from ubxtranslator import predefined
# from ubxtranslator import core

port = serial.Serial('/dev/rtk', baudrate=38400, timeout=1)
gps = UbloxGps(port)

def run():

    try:
        print("Listening for UBX Messages")
        while True:
            try:
                geo = gps.geo_coords()
                print("Longitude: ", geo.lon) 
                print("Latitude: ", geo.lat)
                print("Heading of Motion: ", geo.headMot)
            except (ValueError, IOError) as err:
                print(err)

            try: 
                print('NAV-VALNED')
                # gps.send_message(sp.NAV_CLS, gps.nav_ms.get('VALNED'))
                gps.send_message(NAV_CLS, gps.nav_ms.get('PVT'))
                parse_tool = core.Parser([NAV_CLS])
                cls_name, msg_name, payload = parse_tool.receive_from(port)
                valned = gps.scale_NAV_VALNED(nav_payload = payload)
            except (ValueError, IOError) as err:
                print(err)


            try:
                stat = gps.esf_status()
                print(stat)
            except error as e:
                print(e)
            
            try:
                nav_att = gps.scale_NAV_ATT()
                print(nav_att)
            except Exception as e:
                print(e)

            try:
                nmea = gps.stream_nmea()
                print(nmea)
            except Exception as e:
                print(e)

            # try:
            #     raw = gps.esf_raw_measures()
            #     print(raw)
            # except Exception as e:
            #     print(e)
            
                

    finally:
        port.close()


if __name__ == '__main__':
    run()