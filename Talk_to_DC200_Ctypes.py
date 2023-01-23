import ctypes
import os
import time
import sys

# If you're using Python 3.7 or older change add_dll_directory to chdir
if sys.version_info < (3, 8):
    os.chdir(r"C:\Program Files\IVI Foundation\VISA\Win64\Bin")
else:
    os.add_dll_directory(r"C:\Program Files\IVI Foundation\VISA\Win64\Bin")

#Load DLL library
#os.add_dll_directory("C:\Program Files\IVI Foundation\VISA\Win64\Bin")
LIBRARY=ctypes.cdll.LoadLibrary("TLDC2200_64.dll")

#Connect to device
# !!! In the USB number the serial number (M00...) needs to be changed to the one of the connected device.
DEVSESSION = ctypes.c_int()
LIBRARY.TLDC2200_init(b"USB0::0x1313::0x80C8::M00447336::INSTR", False, False, ctypes.byref(DEVSESSION))
print("Device connected.")

class DC2200():

    def __init__(self):

        """
        DEVSESSION:
        0-Constant current
        1- PWM mode
        2-External modulation
        3-Brightness mode
        4-Pulse mode
        5-Internal modulation
        6-TTL modulation

        """
        pass


    def constant_current_mode(self, current):
        #Constant Current (CC) mode
        # Make CC settings
        LIBRARY.TLDC2200_setOperationMode(DEVSESSION, 0)
        LIBRARY.TLDC2200_setConstCurrent(DEVSESSION, ctypes.c_float(current))
        #Switch LED on
        self.switch_on_led()
        time.sleep(1)
        #Measure applied LED current
        appl_current = ctypes.c_double()
        LIBRARY.TLDC2200_get_led_current_measurement(DEVSESSION, ctypes.byref(appl_current))
        print("Applied LED current: ", appl_current.value)
        time.sleep(1)
        self.switch_off_led()

    def switch_on_led(self):
        LIBRARY.TLDC2200_setLedOnOff(DEVSESSION, True)

    def switch_off_led(self):
        LIBRARY.TLDC2200_setLedOnOff(DEVSESSION, False)

    def change_led_current(self, current):
        #Change LED current
        LIBRARY.TLDC2200_setConstCurrent(DEVSESSION, ctypes.c_float(current))
        appl_current = ctypes.c_double()
        LIBRARY.TLDC2200_get_led_current_measurement(DEVSESSION, ctypes.byref(appl_current))
        print("Applied LED current: ", appl_current.value)

    def pulse_width_pulsation_mode(self, count, current, duty_cycle, frequency):
        #Pulse Width Modulation (PWM) mode
        #Make PWM settings
        LIBRARY.TLDC2200_setOperationMode(DEVSESSION, 1)
        LIBRARY.TLDC2200_setPWMCounts(DEVSESSION, count)
        LIBRARY.TLDC2200_setPWMCurrent(DEVSESSION, ctypes.c_float(current))
        LIBRARY.TLDC2200_setPWMDutyCycle(DEVSESSION, duty_cycle)
        LIBRARY.TLDC2200_setPWMFrequency(DEVSESSION, frequency)
        #Measure applied LED current 10 times
        self.switch_on_led()
        for x in range(0, 10):
            LIBRARY.TLDC2200_get_led_current_measurement(DEVSESSION, ctypes.byref(current))
            print("Applied current: ", current.value)
        self.switch_off_led()

    def pulse_modulation_mode(self, brigthness, on_time, off_time):
        #Pulse Modulation (PM) mode
        #Make PM settings
        LIBRARY.TLDC2200_setOperationMode(DEVSESSION, 5)
        LIBRARY.TLDC2200_setPMBrightness(DEVSESSION, brigthness)
        LIBRARY.TLDC2200_setPMONTime(DEVSESSION, on_time)
        LIBRARY.TLDC2200_setPMOFFTime(DEVSESSION, off_time)
        #Switch LED on
        self.switch_on_led()
        time.sleep(1)
        self.switch_off_led()

    def set_brigthness(self, brigthness):
        LIBRARY.TLDC2200_setOperationMode(DEVSESSION, 3)
        LIBRARY.TLDC2200_setMBrightness(DEVSESSION, brigthness)

    def disconnect(self):
        #Close device connection
        LIBRARY.TLDC2200_close(DEVSESSION)