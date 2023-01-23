SIMULATION = False

if SIMULATION == False:
    import nidaqmx
    from Ressources_scripts import talk_to_elliptec_devices as motor
    from Ressources_scripts import PMA100 as sensor
    from Ressources_scripts import coherent_laser as laser
    from Ressources_scripts import PMA100
if SIMULATION == True:
    from Ressources_scripts import Photodiode_Simulation as nidaqmx
    from Ressources_scripts import Motor_Simulation as motor
    from Ressources_scripts import Laser_Simulation as laser

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QSpinBox, QPushButton, QGridLayout, QGraphicsView
from PySide2.QtCore import QTimer
from PySide2.QtCore import QThread, QObject, Signal
import sys, os
from pyqtgraph import PlotWidget, plot
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import ticker
import numpy as np
import time
import random

CUR_DIR = os.path.dirname(__file__)

ROOT = Path(f"{CUR_DIR}/DATA")
ROOT.mkdir(exist_ok=True)
POWER_METER= PMA100.PMA100()
POWER_METER.Connect()

class Timer_Measure(QObject):
    finished=Signal()
    end=Signal()
    delay=Signal(object)
    update=Signal(object, object)
    close_script=Signal()

    def __init__(self, send_timer, wavelength, theta):
        super().__init__()
        self.timer=send_timer*60
        self.list_of_wavelength=wavelength
        self.list_of_angle=theta

    def run(self):

        for wavelength in self.list_of_wavelength:
            laser.Chameleon().setWavelengthBlocking(int(wavelength))
            laser.Chameleon().openShutterBlocking()
            print("wavelength= ", wavelength)
            self.wavelength = wavelength
            for theta in self.list_of_angle:
                print("Theta: ", theta)
                motor.RotationMount().spin_to_position(position=int(theta))
                self.theta=theta
                self.update.emit(self.wavelength, self.theta)

                print("Timer: ", self.timer)
                start = round(time.time(), 1)
                print("Start time:", start)
                end = round(time.time(), 1)
                delay = round((end - start), 1)
                print("Delay: ", delay)
                while delay < self.timer:
                    self.delay.emit(delay)
                    end = round(time.time(), 1)
                    delay = round((end - start), 1)
                    print("Delay: ", delay)
                    time.sleep(1)
                self.end.emit()

            laser.Chameleon().closeShutterBlocking()

        self.close_script.emit()
        self.finished.emit()


class Main(QWidget):

    def __init__(self):
        super().__init__()
        self.setMinimumSize(800,600)
        self.create_widgets()
        self.list_measuring_power= []
        self.list_measuring_time= []
        self.list_measuring_power_sensor = []

        self.plotting = QTimer()
        self.plotting.setInterval(100)
        self.plotting.timeout.connect(self.measure)

        status = laser.Chameleon().queryShutterStatus()

        if str(status) == "b'1'":
            laser.Chameleon().closeShutterBlocking()
            print("Laser closed")

    @property
    def wavelength_start(self):
        return self.spin_wavelength_start.value()
    @property
    def wavelength_end(self):
        return self.spin_wavelength_end.value()
    @property
    def wavelength_step(self):
        return self.spin_wavelength_step.value()
    @property
    def angle_start(self):
        return self.spin_angle_start.value()
    @property
    def angle_end(self):
        return self.spin_angle_end.value()
    @property
    def angle_step(self):
        return self.spin_angle_step.value()
    @property
    def time(self):
        return self.spin_time.value()

    def create_widgets(self):
        """
        This function generates all the widgets
        :return: Bool
        """
        self.main_layout= QGridLayout(self)
        self.main_layout.setSpacing(1)
        self.main_layout.setContentsMargins(0,0,0,0)



        self.label_time=QLabel("Time: ")
        self.spin_time=QSpinBox()
        self.spin_time.setRange(1,1000)
        self.spin_time.setSingleStep(1)
        self.spin_time.setSuffix(" min.")


        self.label_angle_start = QLabel("Start angle: ")
        self.label_angle_end = QLabel("End angle: ")
        self.label_angle_step = QLabel("Step angle: ")
        self.spin_angle_start = QSpinBox()
        self.spin_angle_start.setRange(0,360)
        self.spin_angle_start.setSingleStep(1)
        self.spin_angle_start.setSuffix(" °")
        self.spin_angle_end = QSpinBox()
        self.spin_angle_end.setRange(0,360)
        self.spin_angle_end.setSingleStep(1)
        self.spin_angle_end.setSuffix(" °")
        self.spin_angle_step = QSpinBox()
        self.spin_angle_step.setRange(0,360)
        self.spin_angle_step.setSingleStep(1)
        self.spin_angle_step.setSuffix(" °")

        self.label_wavelength_start = QLabel("Start wavelength: ")
        self.label_wavelength_end = QLabel("End wavelength: ")
        self.label_wavelength_step = QLabel("Step wavelength: ")
        self.spin_wavelength_start = QSpinBox()
        self.spin_wavelength_start.setRange(680, 1080)
        self.spin_wavelength_start.setSingleStep(5)
        self.spin_wavelength_start.setSuffix(" nm")
        self.spin_wavelength_end = QSpinBox()
        self.spin_wavelength_end.setRange(680, 1080)
        self.spin_wavelength_end.setSingleStep(5)
        self.spin_wavelength_end.setSuffix(" nm")
        self.spin_wavelength_step = QSpinBox()
        self.spin_wavelength_step.setRange(0, 100)
        self.spin_wavelength_step.setSingleStep(1)
        self.spin_wavelength_step.setSuffix(" nm")

        self.label_live_power = QLabel("Live power value: ")
        self.label_live_power_value = QLabel("")

        self.button_go = QPushButton("Go !")

        self.live_power=PlotWidget()
        self.live_power.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        self.main_layout.addWidget(self.live_power, 0, 0, 10, 10)

        self.main_layout.addWidget(self.label_time, 0, 11, 1, 1)
        self.main_layout.addWidget(self.spin_time, 0, 13, 1, 1)

        self.main_layout.addWidget(self.label_angle_start, 2, 10, 1, 1)
        self.main_layout.addWidget(self.spin_angle_start, 2, 11, 1, 1)
        self.main_layout.addWidget(self.label_angle_end, 2, 12, 1, 1)
        self.main_layout.addWidget(self.spin_angle_end, 2, 13, 1, 1)
        self.main_layout.addWidget(self.label_angle_step, 2, 14, 1, 1)
        self.main_layout.addWidget(self.spin_angle_step, 2, 15, 1, 1)

        self.main_layout.addWidget(self.label_wavelength_start, 3, 10, 1, 1)
        self.main_layout.addWidget(self.spin_wavelength_start, 3, 11, 1, 1)
        self.main_layout.addWidget(self.label_wavelength_end, 3, 12, 1, 1)
        self.main_layout.addWidget(self.spin_wavelength_end, 3, 13, 1, 1)
        self.main_layout.addWidget(self.label_wavelength_step, 3, 14, 1, 1)
        self.main_layout.addWidget(self.spin_wavelength_step, 3, 15, 1, 1)

        self.main_layout.addWidget(self.label_live_power, 4, 10, 1, 1)
        self.main_layout.addWidget(self.label_live_power_value, 4, 13, 1, 1)

        self.main_layout.addWidget(self.button_go, 6, 11, 2, 2)

        self.button_go.clicked.connect(self.run)


        self.spin_angle_end.setValue(10)
        self.spin_angle_step.setValue(10)
        self.spin_wavelength_end.setValue(690)
        self.spin_wavelength_step.setValue(10)

        return True

    def save_data(self, data_x, data_y, data_y2, wavelength, theta):
        """
        This function saves the data of the current wavelength in a .txt file located in ROOT
        :param data_x: list
        :param data_y: list
        :param wavelength: int
        :return:None
        """
        file = ROOT / f"{wavelength}_{theta}.txt"
        file.touch()
        i=0
        head_data = f"time (s) \t Photodiode current (mV) \t Powermeter sensor (mW)\n"
        with open(file, "w") as w:
            w.write(head_data)
        for n in data_x:
            data = f"{data_x[i]} \t {data_y[i]} \t {data_y2[i]}\n"
            with open(file, "a") as a:
                a.write(data)
            i+=1

        #Si trop lent, faire une sauvegarde dans le fichier pour chaque couple x, y (pour vider la mémoire)

    def save_figure(self, x, y, y2, wavelength, theta):
        """
        This function saves the plot of all the data for the current wavelength as a png file in ROOT
        :param x: array
        :param y:array
        :param wavelength: int
        :return:None
        """

        fig, ax = plt.subplots()
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter(
            '%.1e'))  # here %.1e is used to put scientific notation  with 1 significative value
        ax.xaxis.set_major_formatter(
            ticker.FormatStrFormatter('%.0f'))  # here %.0f is used to put decimal with 0 significative value
        ax.xaxis.set_major_locator(ticker.MaxNLocator(10))
        ax.xaxis.set_minor_locator(ticker.MaxNLocator(100))
        ax.yaxis.set_major_locator(ticker.MaxNLocator(6))
        ax.plot(x, y, color='red')
        ax.plot(x, y2, color='black')
        plt.xlabel('Time / min.')
        plt.ylabel('Power / mV')
        fig.savefig(ROOT / f"{wavelength}_{theta}.png")

    def run(self):

        print(ROOT)
        list_of_angle=self.define_angle()
        list_of_wavelength=self.define_wavelength()
        print("list_of_angle:", list_of_angle)
        print("list_of_wavelength: ", list_of_wavelength)
        POWER_METER.Clear()
        POWER_METER.Set_Zero()

        self.delay = 0
        #self.plotting.start()

        self.thread = QThread()
        time_to_send = self.time
        self.worker = Timer_Measure(send_timer=time_to_send, wavelength=list_of_wavelength, theta=list_of_angle)
        self.worker.moveToThread(self.thread)
        self.worker.delay.connect(self.set_delay)
        self.worker.update.connect(self.update)
        self.worker.end.connect(self.end_of_measure)
        self.worker.close_script.connect(self.close_script)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def close_script(self):
        time.sleep(2)
        sys.exit(app.exec())

    def update(self, wavelength, theta):
        print("")
        self.wavelength=wavelength
        self.theta=theta

    def set_delay(self, delay):
        self.delay=delay
        self.measure()


    def end_of_measure(self):

        # Changer de couleur pour cahque tétha et faire la mise à jour en temps réel du graph
        self.save_data(data_x=self.list_measuring_time, data_y=self.list_measuring_power, data_y2=self.list_measuring_power_sensor, wavelength=self.wavelength,
                       theta=self.theta)
        self.save_figure(x=self.list_measuring_time, y=self.list_measuring_power, y2=self.list_measuring_power_sensor, wavelength=self.wavelength,
                         theta=self.theta)
        self.list_measuring_power.clear()
        self.list_measuring_time.clear()
        self.list_measuring_power_sensor.clear()
        self.live_power.clear()
        time.sleep(0.1)

    def measure(self):
        print("MEASURE")
        y_photodiode = self.read_photodiode()
        x_sensor, y_sensor = self.read_PMA100()
        y_sensor_corr = y_sensor*1000
        y_sensor_corr = round(y_sensor_corr, 1)
        self.plot(x=self.delay, y=y_photodiode, y2=y_sensor_corr)


    def define_angle(self):
        """
        This function generates the list of all the angle to measure
        :return: list
        """
        temp_value =int((self.angle_end-self.angle_start)/self.angle_step)
        print("temp_value= ", temp_value)
        angle=self.angle_start
        list_of_angle=[angle]
        for n in range(abs(temp_value)):
            if self.angle_start>self.angle_end:
                angle= angle - self.angle_step
                list_of_angle.append(angle)
            else:
                angle = angle + self.angle_step
                list_of_angle.append(angle)
        return list_of_angle

    def define_wavelength(self):
        """
        This function generates the list of all the wavelength to measure
        :return: list
        """
        temp_value =int((self.wavelength_end-self.wavelength_start)/self.wavelength_step)
        print("temp_value= ", temp_value)
        wavelength=self.wavelength_start
        list_of_wavelength=[wavelength]
        for n in range(abs(temp_value)):
            if self.angle_start>self.angle_end:
                wavelength= wavelength - self.wavelength_step
                list_of_wavelength.append(wavelength)
            else:
                wavelength = wavelength + self.wavelength_step
                list_of_wavelength.append(wavelength)
        return list_of_wavelength

    def read_photodiode(self):
        """
        This function reads the photodiode and returns the mean value
        :return: flaot
        """
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan("Dev1/ai1", max_val=5, min_val=-5)
            # data = task.read()
            in_stream = task.in_stream

            data = in_stream.read(number_of_samples_per_channel=10)
            #print('1 Channel N Samples Read: ')
            # data = task.read(number_of_samples_per_channel=10)
            #print("len(data): ", len(data),"type(data): ", type(data))
            #"print("data", data)
            data = np.mean(data)
            #"print("Mean data", data)
            return data

    def read_PMA100(self):
        x, y=POWER_METER.Read_Power()
        return x, y

    def plot(self, x, y, y2):
        """
        This function plots the power vs time on the QGraphicview
        :param x: array
        :param y: array
        :return: None
        """
        print("Plot")
        self.list_measuring_power_sensor.append(y2)
        self.list_measuring_power.append(y)
        self.list_measuring_time.append(x)
        self.live_power.setLabel("left", units="power / mV")
        self.live_power.setLabel("bottom", units="Time / s")
        self.live_power.plot(self.list_measuring_time, self.list_measuring_power, pen="r", symbol="o", symbolPen="r",
                        symbolBrush=0.5, show=True)
        self.live_power.plot(self.list_measuring_time, self.list_measuring_power_sensor, pen="y", symbol="o", symbolPen="y",
                        symbolBrush=0.5, show=True)

app = QApplication(sys.argv)
app.setStyleSheet('''
    QWidget {
    font-size: 30 px;
    }
''')

myApp = Main()
myApp.show()
sys.exit(app.exec())

try:
    sys.exit(app.exec())
except SystemExit:
    print('Closing Windows')