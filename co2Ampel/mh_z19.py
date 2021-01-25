# -*- coding: utf-8 -*-
# original: https://raw.githubusercontent.com/UedaTakeyuki/slider/master/mh_z19.py
#
# © Takeyuki UEDA 2015 -

import serial
import time
import subprocess
import traceback
import getrpimodel
import struct
import platform
import argparse
import sys
import json
import os.path

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)#BCM

# Hier werden die Ausgangs-Pin deklariert, an dem die LEDs angeschlossen sind.
LED_ROT = 22 #25
LED_GRUEN = 18 #24
LED_BLAU = 16 #23

GPIO.setup(LED_ROT, GPIO.OUT, initial= GPIO.LOW)
GPIO.setup(LED_GRUEN, GPIO.OUT, initial= GPIO.LOW)
GPIO.setup(LED_BLAU, GPIO.OUT, initial= GPIO.LOW)

# setting
version = "2.6.3"
pimodel        = getrpimodel.model
pimodel_strict = getrpimodel.model_strict()

if os.path.exists('/dev/serial0'):
  partial_serial_dev = 'serial0'
elif pimodel == "3 Model B" or pimodel_strict == "Zero W":
  partial_serial_dev = 'ttyS0'
else:
  partial_serial_dev = 'ttyAMA0'

serial_dev = '/dev/%s' % partial_serial_dev
#stop_getty = 'sudo systemctl stop serial-getty@%s.service' % partial_serial_dev
#start_getty = 'sudo systemctl start serial-getty@%s.service' % partial_serial_dev

# major version of running python
p_ver = platform.python_version_tuple()[0]

def start_getty():
  start_getty = ['sudo', 'systemctl', 'start', 'serial-getty@%s.service' % partial_serial_dev]
  p = subprocess.call(start_getty)

def stop_getty():
  stop_getty = ['sudo', 'systemctl', 'stop', 'serial-getty@%s.service' % partial_serial_dev]
  p = subprocess.call(stop_getty)

def set_serialdevice(serialdevicename):
  global serial_dev
  serial_dev = serialdevicename

def connect_serial():
  return serial.Serial(serial_dev,
                        baudrate=9600,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        timeout=1.0)

def mh_z19():
  try:
    ser = connect_serial()
    while 1:
      result=ser.write(b"\xff\x01\x86\x00\x00\x00\x00\x00\x79")
      s=ser.read(9)

      if p_ver == '2':
        if len(s) >= 4 and s[0] == "\xff" and s[1] == "\x86":
        #Ampelfarbe ändern
          if(ord(s[2])*256 + ord(s[3]) > 1000): 
            print("Schlechter CO2-Wert! Bitte Lüften!")
            GPIO.output(LED_ROT,GPIO.HIGH) #LED wird eingeschaltet
            GPIO.output(LED_GRUEN,GPIO.LOW) #LED wird eingeschaltet
            GPIO.output(LED_BLAU,GPIO.LOW) #LED wird eingeschaltet
            time.sleep(10) # Wartemodus fuer 4 Sekunden
            GPIO.cleanup()
          elif(ord(s[2])*256 + ord(s[3]) < 800):
            print("Gute Raumluft!")
            GPIO.output(LED_ROT,GPIO.LOW) #LED wird eingeschaltet
            GPIO.output(LED_GRUEN,GPIO.HIGH) #LED wird eingeschaltet
            GPIO.output(LED_BLAU,GPIO.LOW) #LED wird eingeschaltet
            time.sleep(10) #Wartemodus fuer 3 Sekunden
            GPIO.cleanup()
          else :
            print("Raumluft ist in Ordnung. Bitte bald wieder lüften!")
            GPIO.output(LED_ROT,GPIO.LOW) #LED wird eingeschaltet
            GPIO.output(LED_GRUEN,GPIO.LOW) #LED wird eingeschaltet
            GPIO.output(LED_BLAU,GPIO.HIGH) #LED wird eingeschaltet
            time.sleep(10) #Wartemodus fuer 3 Sekunden
            GPIO.cleanup()
             
          return {'co2': ord(s[2])*256 + ord(s[3])}
        break
      else:
        if len(s) >= 4 and s[0] == 0xff and s[1] == 0x86:
        #ampelfarbe ändern
          if(s[2]*256 + s[3] > 1000):
            print("Schlechter CO2-Wert! Bitte lüften!")
            GPIO.output(LED_ROT,GPIO.HIGH) #LED wird eingeschaltet
            GPIO.output(LED_GRUEN,GPIO.LOW) #LED wird eingeschaltet
            GPIO.output(LED_BLAU,GPIO.LOW) #LED wird eingeschaltet
            time.sleep(10) # Wartemodus fuer 4 Sekunden
            GPIO.cleanup()
          
          elif(s[2]*256 + s[3] <= 800) :
            print("Gute Raumluft!")
            GPIO.output(LED_ROT,GPIO.LOW) #LED wird eingeschaltet
            GPIO.output(LED_GRUEN,GPIO.HIGH) #LED wird eingeschaltet
            GPIO.output(LED_BLAU,GPIO.LOW) #LED wird eingeschaltet
            time.sleep(10) #Wartemodus fuer 3 Sekunden
            GPIO.cleanup()
          else :
            print("Raumluft ist in Ordnung. Bitte bald wieder lüften!")
            GPIO.output(LED_ROT,GPIO.LOW) #LED wird eingeschaltet
            GPIO.output(LED_GRUEN,GPIO.LOW) #LED wird eingeschaltet
            GPIO.output(LED_BLAU,GPIO.HIGH) #LED wird eingeschaltet
            time.sleep(10) #Wartemodus fuer 3 Sekunden
            GPIO.cleanup()
          return {'co2': s[2]*256 + s[3]}
        break
  except:
     traceback.print_exc()

def read(serial_console_untouched=False):
  if not serial_console_untouched:
    stop_getty()

  result = mh_z19()

  if not serial_console_untouched:
    start_getty()
  if result is not None:
    return result

def read_all(serial_console_untouched=False):
  if not serial_console_untouched:
    stop_getty()
  try:
    ser = connect_serial()
    while 1:
      result=ser.write(b"\xff\x01\x86\x00\x00\x00\x00\x00\x79")
      s=ser.read(9)

      if p_ver == '2':
        if len(s) >= 9 and s[0] == "\xff" and s[1] == "\x86":
          return {'co2': ord(s[2])*256 + ord(s[3]),
                  'temperature': ord(s[4]) - 40,
                  'TT': ord(s[4]),
                  'SS': ord(s[5]),
                  'UhUl': ord(s[6])*256 + ord(s[7])
                  }
        break
      else:
        if len(s) >= 9 and s[0] == 0xff and s[1] == 0x86:
          return {'co2': s[2]*256 + s[3],
                  'temperature': s[4] - 40,
                  'TT': s[4],
                  'SS': s[5],
                  'UhUl': s[6]*256 + s[7]
                  }
        break
  except:
     traceback.print_exc()

  if not serial_console_untouched:
    start_getty()
  if result is not None:
    return result

def abc_on(serial_console_untouched=False):
  if not serial_console_untouched:
    stop_getty()
  ser = connect_serial()
  result=ser.write(b"\xff\x01\x79\xa0\x00\x00\x00\x00\xe6")
  ser.close()
  if not serial_console_untouched:
    start_getty()

def abc_off(serial_console_untouched=False):
  if not serial_console_untouched:
    stop_getty()
  ser = connect_serial()
  result=ser.write(b"\xff\x01\x79\x00\x00\x00\x00\x00\x86")
  ser.close()
  if not serial_console_untouched:
    start_getty()

def span_point_calibration(span, serial_console_untouched=False):
  if not serial_console_untouched:
    stop_getty()
  ser = connect_serial()
  if p_ver == '2':
    b3 = span / 256;
  else:
    b3 = span // 256;   
  byte3 = struct.pack('B', b3)
  b4 = span % 256; byte4 = struct.pack('B', b4)
  c = checksum([0x01, 0x88, b3, b4])
  request = b"\xff\x01\x88" + byte3 + byte4 + b"\x00\x00\x00" + c
  result = ser.write(request)
  ser.close()
  if not serial_console_untouched:
    start_getty()

def zero_point_calibration(serial_console_untouched=False):
  if not serial_console_untouched:
    stop_getty()
  ser = connect_serial()
  request = b"\xff\x01\x87\x00\x00\x00\x00\x00\x78"
  result = ser.write(request)
  ser.close()
  if not serial_console_untouched:
    start_getty()

def detection_range_10000(serial_console_untouched=False):
  if not serial_console_untouched:
    stop_getty()
  ser = connect_serial()
  request = b"\xff\x01\x99\x00\x00\x00\x27\x10\x2F"
  result = ser.write(request)
  ser.close()
  if not serial_console_untouched:
    start_getty()

def detection_range_5000(serial_console_untouched=False):
  if not serial_console_untouched:
    stop_getty()
  ser = connect_serial()
  request = b"\xff\x01\x99\x00\x00\x00\x13\x88\xcb"
  result = ser.write(request)
  ser.close()
  if not serial_console_untouched:
    start_getty()

def detection_range_2000(serial_console_untouched=False):
  if not serial_console_untouched:
    stop_getty()
  ser = connect_serial()
  request = b"\xff\x01\x99\x00\x00\x00\x07\xd0\x8F"
  result = ser.write(request)
  ser.close()
  if not serial_console_untouched:
    start_getty()

def checksum(array):
  return struct.pack('B', 0xff - (sum(array) % 0x100) + 1)

if __name__ == '__main__':
#  value = read()
#  print (value)
  parser = argparse.ArgumentParser(
    description='''return CO2 concentration as object as {'co2': 416}''',
  )
  parser.add_argument("--serial_device",
                      type=str,
                      help='''Use this serial device file''')

  parser.add_argument("--serial_console_untouched",
                      action='store_true',
                      help='''Don't close/reopen serial console before/after sensor reading''')


  group = parser.add_mutually_exclusive_group()

  group.add_argument("--version",
                      action='store_true',
                      help='''show version''')
  group.add_argument("--all",
                      action='store_true',
                      help='''return all (co2, temperature, TT, SS and UhUl) as json''')
  group.add_argument("--abc_on",
                      action='store_true',
                      help='''Set ABC functionality on model B as ON.''')
  group.add_argument("--abc_off",
                      action='store_true',
                      help='''Set ABC functionality on model B as OFF.''')
  parser.add_argument("--span_point_calibration",
                      type=int,
                      help='''Call calibration function with SPAN point''')
  parser.add_argument("--zero_point_calibration",
                      action='store_true',
                      help='''Call calibration function with ZERO point''')
  parser.add_argument("--detection_range_10000",
                      action='store_true',
                      help='''Set detection range as 10000''')
  parser.add_argument("--detection_range_5000",
                      action='store_true',
                      help='''Set detection range as 5000''')
  parser.add_argument("--detection_range_2000",
                      action='store_true',
                      help='''Set detection range as 2000''')

  args = parser.parse_args()

  if args.serial_device is not None:
    set_serialdevice(args.serial_device)

  if args.abc_on:
    abc_on(args.serial_console_untouched)
    print ("Set ABC logic as on.")
  elif args.abc_off:
    abc_off(args.serial_console_untouched)
    print ("Set ABC logic as off.")
  elif args.span_point_calibration is not None:
    span_point_calibration(args.span_point_calibration, args.serial_console_untouched)
    print ("Call Calibration with SPAN point.")
  elif args.zero_point_calibration:
    print ("Call Calibration with ZERO point.")
    zero_point_calibration(args.serial_console_untouched)
  elif args.detection_range_10000:
    detection_range_10000(args.serial_console_untouched)
    print ("Set Detection range as 10000.")
  elif args.detection_range_5000:
    detection_range_5000(args.serial_console_untouched)
    print ("Set Detection range as 5000.")
  elif args.detection_range_2000:
    detection_range_2000(args.serial_console_untouched)
    print ("Set Detection range as 2000.")
  elif args.version:
    print (version)
  elif args.all:
    value = read_all(args.serial_console_untouched)
    print (json.dumps(value))
  else:
    value = read(args.serial_console_untouched)
    print (json.dumps(value))

  sys.exit(0)
