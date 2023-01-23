from PySide6.QtWidgets import QWidget, QApplication, QHBoxLayout, QVBoxLayout, QGraphicsView, QLabel, QSpinBox, QDial, QPushButton, QStyle, QMessageBox, QFileDialog
from pyqtgraph import PlotWidget
from PySide6.QtCore import QObject, QThread, Signal
import numpy as np
import json
import sys
from pathlib import Path
import time
import Talk_to_DC200_Ctypes as controller
import talk_to_spectro as spectro
from random import randrange
import pandas as pd

COLOR={1:"blue", 2:"cyan",3:"green", 4:"yellow", 5:"orange", 6:"magenta", 7:"red", 8:"darkMagenta", 9:"darkGreen", 10:"darkCyan"}

class Calibrate(QObject):
    signal_to_plot = Signal(object, object, object, object)
    finished = Signal()
    def __init__(self, illumination_time):
        super().__init__()
        self.illumination_time=illumination_time

    def run(self):
        wavelength, intensity = spectro.Maya(integration_time=self.illumination_time).get_spectrum()
        print(wavelength, intensity)
        self.signal_to_plot.emit(wavelength, intensity, "fluo_spectra", "Live view")
        self.finished.emit()

    def stop(self):
        self.finished.emit()

class Measure(QObject):
    signal_to_plot= Signal(object, object, object, object)
    finished= Signal()
    pop_up = Signal()

    def __init__(self, illumination_time, experiment_time, time_between_measures, data_root):
        super().__init__()
        self.raw_data={}
        self.counter=0
        self.data_root=Path(data_root)
        print(self.data_root)
        print(type(self.data_root))
        self.create_json_data_file()

        self.illumination_time=illumination_time
        self.experiment_time=experiment_time
        self.time_between_measures=time_between_measures
        self.number_of_measures=self.experiment_time/((self.illumination_time/60000)+self.time_between_measures)
        print("illumination_time", illumination_time)
        print("experiment_time", experiment_time)
        print("time_between_measures", time_between_measures)
        print(self.number_of_measures)
        self.x_integral=[]
        self.y_integral=[]


    def create_json_data_file(self):
        self.raw_data_file=self.data_root / "raw_data.json"
        self.raw_data_file.touch()

    def save_data(self):

        with open(self.raw_data_file, "r") as r:
            raw_data=json.load(r)
        root= self.data_root / "all_data.xlsx"
        root_spectra_txt= self.data_root / "spectra_data.txt"
        root_integrals_txt = self.data_root / "integrals_data.txt"

        time_to_save=[]
        integral_to_save=[]

        temp ={}
        data={}
        data_to_save= pd.DataFrame(data)
        for time in raw_data:
            wavelength=raw_data[f"{time}"]["Wavelength"]
            intensity=raw_data[f"{time}"]["Intensity"]
            integral=raw_data[f"{time}"]["Integral"]
            data_to_save[f"{time} min _ Wavelength / nm"]=pd.Series(wavelength)
            data_to_save[f"{time} min _ Fluorescence / cps"]=pd.Series(intensity)
            #data_to_save[f"{time} min _ Integral of fluorescence / cps"]=pd.Series(integral)
            temp.update({f"{time} min ":data_to_save})
            time_to_save.append(time)
            integral_to_save.append(integral)

        data_2= {
            'Time / min.': pd.Series(time_to_save),
            'Fluorescence integral / cps': pd.Series(integral_to_save)
        }
        data_to_save_2=pd.DataFrame(data_2)
        with open(root_spectra_txt, 'a') as b:
            b.write(data_to_save.to_string())

        with open(root_integrals_txt, 'a') as b:
            b.write(data_to_save_2.to_string())



        with pd.ExcelWriter(root) as writer:
            for key, value in temp.items():
                value.to_excel(writer, sheet_name="Fluorescence spectra")
            data_to_save_2.to_excel(writer, sheet_name="Integrals")

    def run(self):
        while self.counter <self.number_of_measures:
            print("Measure #", self.counter)
            self.step_1()
            self.step_2()
            self.step_3()
            self.step_4()
            self.counter+=1
            time.sleep(self.time_between_measures*60)
        self.step_5()
        self.save_data()
        self.pop_up.emit()
        self.finished.emit()

    def step_1(self):
        """Switch on ligth"""
        controller.DC2200().switch_on_led()
        print("LED Switch on")
        time.sleep(1)

    def step_2(self):
        """Switch on USB MAYAPro & record spectrum & save data"""
        wavelength, intensities= spectro.Maya(integration_time=self.illumination_time).get_spectrum()

        #For testing purposes
        """wavelength =[]
        intensities =[]
        counter_for_testing =0
        for n in range(1100):
            wavelength.append(counter_for_testing)
            value = (np.sin(counter_for_testing))*((randrange(1, 100,5 ))/100)
            intensities.append(value)
            counter_for_testing +=1
        """
        wavelength =wavelength.tolist()
        intensities=intensities.tolist()
        print("#"*1000)
        print(type(wavelength))
        print("#" * 1000)

        self.time_of_measure=self.counter*self.time_between_measures

        self.y_integral.append(np.trapz(intensities,wavelength))
        self.x_integral.append(self.time_of_measure)
        print("self.y_integral=", self.y_integral)
        print("self.x_integral=", self.x_integral)

        self.integral_to_save=self.y_integral[-1]

        self.raw_data={self.time_of_measure:{"Wavelength": wavelength, "Intensity":intensities, "Integral":self.integral_to_save}}
        if self.counter == 0:
            with open(self.raw_data_file, "w") as w:
                json.dump(self.raw_data, w)
        else:
            with open(self.raw_data_file, "r") as r:
                data_to_update=json.load(r)
                print("data_to_update", data_to_update)
                data_to_update.update(self.raw_data)
                print("Updated data", data_to_update)
            with open(self.raw_data_file, "w") as w:
                json.dump(data_to_update, w)
        self.x=wavelength
        self.y=intensities

    def step_3(self):
        """Switch off light"""
        controller.DC2200().switch_off_led()
        print("LED switch off")

    def step_4(self):
        """Send signal to plot"""
        self.signal_to_plot.emit(self.x_integral, self.y_integral, "fluo_integration", self.time_of_measure)

        self.signal_to_plot.emit(self.x, self.y, "fluo_spectra", self.counter)
        print("Data processed")

    def step_5(self):
        """Processed data and close"""
        print("Data processed")


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setMinimumSize(800,600)
        self.setWindowTitle("PyLEDKinetic")

        self.main=QHBoxLayout(self)
        self.create_widgets()
        self.set_root()

    def set_root(self):
        self.data_root = QFileDialog.getExistingDirectory(caption="Please select the folder to save datas")
        print(self.data_root)

    def create_widgets(self):
        self.graphical_data=QVBoxLayout()
        self.parameters=QVBoxLayout()

        self.btn_go = QPushButton("Start")
        self.btn_go.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.parameters_up=QHBoxLayout()
        self.parameters_middle=QHBoxLayout()
        self.parameters_bottom = QHBoxLayout()

        self.main.addLayout(self.graphical_data)
        self.main.addLayout(self.parameters)

        self.parameters.addLayout(self.parameters_up)
        self.parameters.addLayout(self.parameters_middle)
        self.parameters.addLayout(self.parameters_bottom)

        self.fluo_integration=PlotWidget()
        self.fluo_integration.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.fluo_spectra=PlotWidget()
        self.fluo_spectra.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)


        self.graphical_data.addWidget(self.fluo_integration)
        self.graphical_data.addWidget(self.fluo_spectra)
        self.btn_switch_state_led=QPushButton("LED OFF")
        self.btn_switch_state_led.setCheckable(True)
        self.btn_switch_state_led.setStyleSheet("""QPushButton 
                                                {
                                                    background-color: red;}
                                                   QPushButton::checked
                                                {
                                                    background-color: green;
                                                    border: 0;    
                                                     }""")


        self.label_acq_time=QLabel("Acquisition time")
        self.spb_acq_time=QSpinBox()
        self.spb_acq_time.setRange(10, 10000)
        self.spb_acq_time.setSuffix("ms")
        self.label_step_time=QLabel("Time between 2 measures")
        self.spb_step_time=QSpinBox()
        self.spb_step_time.setRange(1, 3600)
        self.spb_step_time.setSuffix("min")
        self.label_time_of_experiment=QLabel("Experimental time")
        self.spb_time_of_experiment_hours=QSpinBox()
        self.spb_time_of_experiment_hours.setSuffix("h")
        self.spb_time_of_experiment=QSpinBox()
        self.spb_time_of_experiment.setRange(1, 100000)
        self.spb_time_of_experiment.setSuffix("min")

        self.dial_power=QDial()
        self.dial_power.setRange(0,1000)
        self.dial_power.setNotchesVisible(True)
        #self.dial_power.setNotchTarget(10) # number of pixel between notches
        self.dial_power.setSingleStep(5)
        self.dial_power.valueChanged.connect(lambda : self.dial_method())
        self.label_dial_power=QLabel("Current Power % : 0")


        self.parameters_up.addWidget(self.label_acq_time)
        self.parameters_up.addWidget(self.spb_acq_time)
        self.parameters_bottom.addWidget(self.label_step_time)
        self.parameters_bottom.addWidget(self.spb_step_time)
        self.parameters_middle.addWidget(self.label_time_of_experiment)
        self.parameters_middle.addWidget(self.spb_time_of_experiment_hours)
        self.parameters_middle.addWidget(self.spb_time_of_experiment)
        self.parameters.addWidget(self.dial_power)
        self.parameters.addWidget(self.label_dial_power)
        self.parameters.addWidget(self.btn_switch_state_led)
        self.parameters.addWidget(self.btn_go)

        self.btn_go.clicked.connect(self.run_experiment)
        self.btn_switch_state_led.clicked.connect(self.change_led_state)

    def dial_method(self):
        value_dial_power = (self.dial_power.value())/1000
        print(value_dial_power)
        self.label_dial_power.setText("Current Power % : " + str(round(value_dial_power*100,1)))
        controller.DC2200().change_led_current(current=value_dial_power)

    def change_led_state(self):
        self.thread_2=QThread()
        self.worker_2 = Calibrate(illumination_time=self.spb_acq_time.value())
        self.worker_2.moveToThread(self.thread_2)
        self.worker_2.signal_to_plot.connect(self.plot)
        self.thread_2.started.connect(self.worker_2.run)
        self.worker_2.finished.connect(self.thread_2.quit)

        if self.btn_switch_state_led.isChecked() == True:
            controller.DC2200().switch_on_led()
            self.btn_switch_state_led.setText("LED ON")
            self.thread_2.start()

        else:
            controller.DC2200().switch_off_led()
            self.btn_switch_state_led.setText("LED OFF")
            self.fluo_spectra.clear()

    def run_experiment(self):
        self.total_experimental_time = self.spb_time_of_experiment_hours.value() * 60 + self.spb_time_of_experiment.value()
        print("Total experimental time = ", self.total_experimental_time, " min.")
        self.btn_go.setEnabled(False)
        self.spb_acq_time.setEnabled(False)
        self.spb_time_of_experiment.setEnabled(False)
        self.spb_step_time.setEnabled(False)
        self.dial_power.setEnabled(False)
        self.spb_time_of_experiment_hours.setEnabled(False)
        print("Start experiment")
        self.thread = QThread()
        self.worker = Measure(illumination_time=self.spb_acq_time.value(), experiment_time=self.total_experimental_time, time_between_measures=self.spb_step_time.value(), data_root=self.data_root)
        self.worker.moveToThread(self.thread)
        self.worker.signal_to_plot.connect(self.plot)
        self.worker.pop_up.connect(self.ending_pop_up)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def ending_pop_up(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle(f"Measure finished")
        dlg.setText(f"Please copy the data before a new experiment :")
        dlg.exec()

    def plot(self, x, y, name_graph_widget, measure_number):
        if name_graph_widget == "fluo_integration":
            graph_widget=self.fluo_integration
            name = None
            color="Yellow"
            graph_widget.setLabel('left', units="Fluorescence intensity / cps")
            graph_widget.setLabel('bottom', units="Time / min")
        elif name_graph_widget == "fluo_spectra":
            graph_widget=self.fluo_spectra
            name = f'{measure_number}'
            rand_color= randrange(1,10,1)
            color=COLOR[rand_color]
            graph_widget.setLabel('left', units="Fluorescence intensity / cps")
            graph_widget.setLabel('bottom', units="Wavelength / nm")

        x = np.array(x)
        y = np.array(y)

        graph_widget.addLegend()
        graph_widget.setLabel('left', units="Fluorescence intensity / cps")
        #graph_widget.setYRange(0, 64000)
        #graph_widget.setXRange(300, 1100)
        graph_widget.plot(x, y,pen=color, name= name, show=True)






if __name__ == "__main__":
    app = QApplication()
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

    try:
        sys.exit(app.exec())
    except SystemExit:
        print('Closing Windows')


