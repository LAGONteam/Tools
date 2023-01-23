from seabreeze.spectrometers import Spectrometer, list_devices
import numpy as np

DEVICES = list_devices()
print(DEVICES)
SPECTRO = Spectrometer.from_first_available()
print(SPECTRO)

class Maya():

    def __init__(self, integration_time):
        SPECTRO.integration_time_micros(integration_time * 1000)
        print(integration_time)


    def get_spectrum(self):
        wavelength=SPECTRO.wavelengths()
        intensities=SPECTRO.intensities(correct_dark_counts=True, correct_nonlinearity=True)
        print("#"*1000)
        print(type(wavelength))
        print("#" * 1000)
        return wavelength, intensities

    def _data_read_scan(self, number_of_scan, intensity_dark):
        if type(intensity_dark) == int:
            intensity_dark = np.zeros(shape=2068, dtype=int)
        for n in range(int(number_of_scan)):
            wavelength, intensities= self.get_spectrum()
            data = np.zeros(shape=2068, dtype=int)
            intensity = np.zeros(shape=2068, dtype=int)
            print(data)
            for i in range(len(intensities)):
                print("i=", i)
                print(data[i])
                print(intensities[i])
                print(intensity_dark[i])
                data[i]=data[i]+intensities[i]-intensity_dark[i]
                intensity[i]=intensity[i] + intensities[i]
                print(data[i])
            print('#'*100, "\n", data)
        print('dataread', data)
        return wavelength, data, intensity


if __name__ == "__main__":
    a=Maya(100)
    w, i=a.get_spectrum()
    z, r, t= a._data_read_scan(10, 0)
    print("z=", z)
    print("r=", r)
    print("t=", t)

