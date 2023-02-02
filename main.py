import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QLineEdit, QPushButton, QLabel, QDialog, QMessageBox, QFileDialog, QVBoxLayout, QFrame
from PyQt6 import QtCore
from PyQt6.QtGui import QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
import requests
from scipy.interpolate import CubicSpline, interp1d
from math import floor, ceil
import ctypes
import datetime as dt

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('appid56456546')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pogoda")

        layout = QGridLayout()
        search_button = QPushButton("Szukaj")
        search_button.clicked.connect(self.draw_plot)
        save_button = QPushButton("Zapisz")
        save_button.clicked.connect(self.save_fig)
        self.setStyleSheet("background-color : white;")
        search_button.setStyleSheet("background-color : lightcyan; color:black")
        self.search_line = QLineEdit()

        self.figure = plt.figure(figsize=(16, 12), dpi=80)
        self.canvas = FigureCanvasQTAgg(self.figure)
        # self.figure.tight_layout()

        self.infoBox = QWidget()
        infoBoxLayout = QVBoxLayout()
        self.mean_temp = QLabel()
        self.mean_wind_chill = QLabel()
        self.sunrise = QLabel()
        self.sunset = QLabel()

        infoBoxLayout.addWidget(self.mean_temp)
        infoBoxLayout.addWidget(self.mean_wind_chill)
        infoBoxLayout.addWidget(self.sunrise)
        infoBoxLayout.addWidget(self.sunset)
        self.infoBox.setLayout(infoBoxLayout)

        layout.addWidget(self.search_line, 0, 0, 1, 6)
        layout.addWidget(search_button, 0, 6, 1, 2)
        layout.addWidget(save_button, 0, 8, 1, 2)
        layout.addWidget(self.canvas, 1, 0, 10, 8)
        layout.addWidget(self.infoBox, 1, 8, 1, 1)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.setWindowIcon(QIcon("icon.png"))
        self.showMaximized()

    def draw_plot(self):
        self.figure.clear()
        try:
            xdata, xlabels, temperature, wind_chill, sunrise, sunset, wind = self.getData()
        except:


            dial = ErrorDialog()

            if dial.exec() == QMessageBox.accepted:
                self.search_line.clear()
            return

        sunrise = dt.datetime.fromtimestamp(sunrise).strftime('%H:%M:%S')
        sunset = dt.datetime.fromtimestamp(sunset).strftime('%H:%M:%S')

        self.sunrise.setText(f"Wschód słońca: {sunrise}")
        self.sunrise.adjustSize()
        self.sunset.setText(f"Zachód słońca: {sunset}")
        self.sunset.adjustSize()

        temperature = self.kelvinToCelcius(temperature)
        wind_chill = self.kelvinToCelcius(wind_chill)
        wind = self.mps_to_mph(wind)

        temperature_interp_func = CubicSpline(xdata, temperature)
        wind_chill_interp_func = CubicSpline(xdata, wind_chill)
        wind_interp_func = interp1d(xdata, wind)
        x = np.linspace(xdata[0], xdata[-1], 200)
        temperature_interpolated = temperature_interp_func(x)
        wind_chill_interpolated = wind_chill_interp_func(x)
        wind_interpolated = wind_interp_func(x)

        for i in range(len(xlabels)):
            xlabels[i] = xlabels[i][5:-3]
            tmp = xlabels[i][0:5]
            tmp = tmp.split('-')
            tmp = '-'.join(tmp[::-1])
            xlabels[i] = xlabels[i].replace(xlabels[i][0:5], tmp)

        yticks = self.temperatureRange(temperature_interpolated, wind_chill_interpolated, wind)
        print(yticks)

        _mean_temp = np.mean(temperature_interpolated).round(2)
        _mean_wind_chill = np.mean(wind_chill_interpolated).round(2)
        self.mean_temp.setText(f"Średnia temperatura: {_mean_temp}")
        self.mean_wind_chill.setText(f"Średnia odczuwalna temperatura: {_mean_wind_chill}")
        self.mean_temp.adjustSize()
        self.mean_wind_chill.adjustSize()

        ax = self.figure.add_subplot(111)

        self.figure.patch.set_facecolor('paleturquoise')
        ax.set_title(f"Pogoda w miejscowości {self.search_line.text():}", fontsize=20)
        ax.set_facecolor("lightcyan")
        ax.plot(x, wind_chill_interpolated, label=f"Temperatura odczuwalna ($^\circ$C)")
        ax.plot(x, temperature_interpolated, label=f"temperatura interpolowana ($^\circ$C)")
        ax.plot(x, wind_interpolated, label="Wiatr (mph)")

        ax.set_xticks(xdata, xlabels, rotation=45)
        ax.set_ylim(np.min(yticks), np.max(yticks))
        ax.set_yticks(yticks)
        ax.legend(loc="best")
        ax.grid()

        self.canvas.draw()

        self.search_line.clear()

    @staticmethod
    def temperatureRange(temperature, wind_chill, wind):
        _min = min(temperature)
        _max = max(temperature)

        if min(wind_chill) < _min:
            _min = min(wind_chill)

        if min(wind) < _min:
            _min = min(wind)

        if max(wind_chill) > _max:
            _max = max(wind_chill)

        if max(wind) > _max:
            _max = max(wind)

        return np.arange(floor(_min) - 0.5, ceil(_max) + 1.5, 0.5)

    def process_data(self):
        xdata, xlabels, temperature, wind_chill, sunrise, sunset, wind = self.getData()

        return xdata, xlabels, temperature, wind_chill, sunrise, sunset, wind

    def save_fig(self):
        name = QFileDialog.getSaveFileName(self, 'Save File', filter="Image files (*.png)")
        self.figure.savefig(f"{name[0]}")

    def getData(self):
        with open("api_key.txt", 'r') as key:
            api_key = key.read().strip()
            print(api_key)

        print(f"http://api.openweathermap.org/geo/1.0/direct?q={self.search_line.text()}&limit=5&appid={api_key}")
        city_loc = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={self.search_line.text()}&limit=5&appid={api_key}")

        if city_loc.status_code != 200:
            return None


        city_loc = city_loc.json()

        if not city_loc:
            return None

        print(city_loc)
        latitude = round(city_loc[0]['lat'], 2)
        longitude = round(city_loc[0]['lon'], 2)
        weather_data = requests.get(f"http://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&appid={api_key}")
        print(f"http://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&appid={api_key}")

        if weather_data.status_code != 200:
            return None

        weather_data = weather_data.json()

        sunrise = weather_data['city']['sunrise']
        sunset = weather_data['city']['sunset']

        weather_data = weather_data['list']

        temperature = np.empty(40)
        wind_chill = np.empty(40)
        datetime = np.empty(40)
        wind = np.empty(40)
        date_labels = []

        i = 0
        for wd in weather_data:
            datetime[i] = wd['dt']
            date_labels.append(wd['dt_txt'])
            temperature[i] = wd['main']['temp']
            wind_chill[i] = wd['main']['feels_like']
            wind[i] = wd['wind']['speed']
            i += 1

        print(temperature)

        # print(weather_data)
        print(len(temperature))
        return datetime, date_labels, temperature, wind_chill, sunrise, sunset, wind

    @staticmethod
    def kelvinToCelcius(k):
        """
        Zamiana na stopnie Celcjusza
        """
        return k - 273.15

    @staticmethod
    def mps_to_mph(mps):
        """
        Zamiana na mile na godzine
        """
        return mps * 2.23693381



class ErrorDialog(QDialog):
    """
    Informacja o błędzie wyskakująca po wpisaniu nieprawidłowej nazwy miejscowości
    """
    def __init__(self):
        super().__init__()
        layout = QGridLayout()
        self.lbl = QLabel("Nie udało się odszukać podanej miejscowości :(")
        self.btn = QPushButton("Zamknij")
        self.setWindowTitle("Błąd")
        layout.addWidget(self.lbl, 0, 0, 1, 4)
        layout.addWidget(self.btn, 1, 1, 1, 2)
        self.btn.clicked.connect(self.accept)

        self.setLayout(layout)


if __name__ == '__main__':
    weatherApp = QApplication([])
    window = MainWindow()
    weatherApp.exec()
