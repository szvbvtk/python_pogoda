import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QLineEdit, QPushButton, QLabel, QDialog, QMessageBox, QFileDialog
from PyQt6 import QtCore
from PyQt6.QtGui import QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
import requests
from scipy.interpolate import CubicSpline
from math import floor, ceil


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pogoda")

        layout = QGridLayout()
        search_button = QPushButton("Szukaj")
        search_button.clicked.connect(self.draw_plot)
        save_button = QPushButton("Zapisz")
        save_button.clicked.connect(self.save_fig)

        search_button.setStyleSheet("background-color : #018723; color:black")
        self.search_line = QLineEdit()

        self.figure = plt.figure(figsize=(16, 12), dpi=80)
        self.canvas = FigureCanvasQTAgg(self.figure)
        # self.figure.tight_layout()

        layout.addWidget(self.search_line, 0, 0, 1, 1)
        layout.addWidget(search_button, 0, 2, 1, 2)
        layout.addWidget(save_button, 0, 4, 1, 1)
        layout.addWidget(self.canvas, 1, 0, 1, 5)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.setWindowIcon(QIcon("icon.png"))
        self.showMaximized()

    def draw_plot(self):
        self.figure.clear()
        try:
            xdata, xlabels, temperature, wind_chill = self.getData()
        except:


            dial = ErrorDialog()

            if dial.exec() == QMessageBox.accepted:
                self.search_line.clear()
            return

        temperature_interp_func = CubicSpline(xdata, temperature)
        wind_chill_interp_func = CubicSpline(xdata, wind_chill)
        x = np.linspace(xdata[0], xdata[-1], 200)
        temperature_interpolated = temperature_interp_func(x)
        wind_chill_interpolated = wind_chill_interp_func(x)

        for i in range(len(xlabels)):
            xlabels[i] = xlabels[i][5:-3]
            tmp = xlabels[i][0:5]
            tmp = tmp.split('-')
            tmp = '-'.join(tmp[::-1])
            xlabels[i] = xlabels[i].replace(xlabels[i][0:5], tmp)

        yticks = self.temperatureRange(temperature_interpolated, wind_chill_interpolated)
        print(yticks)
        ax = self.figure.add_subplot(111)
        ax.set_title(f"Pogoda w miejscowości {self.search_line.text():}")
        ax.plot(x, wind_chill_interpolated, label="Temperatura odczuwalna")
        ax.plot(x, temperature_interpolated, label="temperatura interpolowana")

        ax.set_xticks(xdata, xlabels, rotation=45)
        ax.set_ylim(np.min(yticks), np.max(yticks))
        ax.set_yticks(yticks)
        ax.legend(loc="best")
        ax.grid()

        self.canvas.draw()

        self.search_line.clear()

    @staticmethod
    def temperatureRange(temperature, wind_chill):
        _min = min(temperature)
        _max = max(temperature)

        if min(wind_chill) < _min:
            _min = min(wind_chill)

        if max(wind_chill) > _max:
            _max = max(wind_chill)

        return np.arange(floor(_min) - 0.5, ceil(_max) + 1.5, 0.5)


    def save_fig(self):
        name = QFileDialog.getSaveFileName(self, 'Save File', filter="Image files (*.png)")
        self.figure.savefig(f"{name[0]}")

    def getData(self):
        api_key = "8864222db203617b56fad931687f7175"
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

        if weather_data.status_code != 200:
            return None

        weather_data = weather_data.json()['list']

        temperature = []
        wind_chill = []
        _datetime = []
        date_labels = []
        for d in weather_data:
            _datetime.append(d['dt'])
            date_labels.append(d['dt_txt'])
            temperature.append(round(self.kelvinToCelcius(d['main']['temp']), 2))
            wind_chill.append(round(self.kelvinToCelcius(d['main']['feels_like']), 2))

        # print(weather_data)
        return _datetime, date_labels, temperature, wind_chill

    @staticmethod
    def kelvinToCelcius(k):
        return k - 273.15


class ErrorDialog(QDialog):
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
