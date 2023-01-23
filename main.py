import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QLineEdit, QPushButton, QLabel
from PyQt6 import QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
import random
import requests
from scipy.interpolate import CubicSpline
from numpy import linspace


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pogoda")

        layout = QGridLayout()
        search_button = QPushButton("Szukaj")
        search_button.clicked.connect(self.draw_plot)
        search_button.setStyleSheet("background-color : #018723; color:black")
        self.search_line = QLineEdit()

        self.figure = plt.figure(figsize=(16, 12), dpi=80)
        self.canvas = FigureCanvasQTAgg(self.figure)
        # self.figure.tight_layout()

        layout.addWidget(search_button, 0, 2, 2, 2)
        layout.addWidget(self.search_line, 0, 0, 2, 2)
        layout.addWidget(self.canvas)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.show()

    def draw_plot(self):
        self.figure.clear()
        xdata, xlabels, y1data, y2data = self.getData()
        temperature_interp = CubicSpline(xdata, y1data)
        x = np.linspace(xdata[0], xdata[-1], 200)
        y = temperature_interp(x)
        print(temperature_interp)
        for i in range(len(xlabels)):
            xlabels[i] = xlabels[i][5:-3]
            tmp = xlabels[i][0:5]
            tmp = tmp.split('-')
            tmp = '-'.join(tmp[::-1])
            xlabels[i] = xlabels[i].replace(xlabels[i][0:5], tmp)


        ax = self.figure.add_subplot(111)
        ax.set_title(f"Pogoda w miejscowości {self.search_line.text():}")
        ax.plot(xdata, y1data, label="temperatura")
        # ax.plot(xdata, y2data, label="temperatura odczuwalna")
        ax.plot(x, y, label="temperatura interpolowana")
        ax.set_xticks(xdata, xlabels, rotation=45)
        # ax.set_ylim(min(y1data), max(y1data))
        # ax.set_xticklabels(rotation=45)
        ax.legend(loc="upper left")
        ax.grid()
        self.canvas.draw()

        self.search_line.clear()

    def getData(self):
        api_key = "8864222db203617b56fad931687f7175"
        city_loc = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={self.search_line.text()}&limit=5&appid={api_key}").json()
        # print(city_loc[0])
        latitude = round(city_loc[0]['lat'], 2)
        longitude = round(city_loc[0]['lon'], 2)
        weather_data = requests.get(f"http://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&appid={api_key}").json()['list']

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
        return (_datetime, date_labels, temperature, wind_chill)

    @staticmethod
    def kelvinToCelcius(k):
        return k - 273.15











weatherApp = QApplication([])
window = MainWindow()
weatherApp.exec()
