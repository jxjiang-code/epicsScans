import sys
import numpy as np
import time
from scipy.optimize import curve_fit
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import QTimer

# Define the error function for Z alignment
def error_function(x, x0, scale, width):
    return scale * (1 + np.tanh((x - x0) / width)) / 2


# Define the Gaussian function for Theta alignment
def gaussian(x, x0, width, scale):
    return scale * np.exp(-((x - x0) ** 2) / (2 * width ** 2))


class DynamicPlot(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dynamic Plot with Alignment Controls")
        self.setGeometry(100, 100, 800, 600)

        # Create main widget
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        # Create layout
        layout = QVBoxLayout(self.main_widget)

        # Create Matplotlib figure and canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Initialize plot
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Dynamic Data")
        self.ax.set_xlabel("X-axis")
        self.ax.set_ylabel("Y-axis")

        # Timer for updating random data
        #self.timer = QTimer(self)
        #self.timer.timeout.connect(self.update_live_plot)
        #self.timer.start(1000)  # Update every 1 second

        # Data for the plot
        self.data = {"x": [], "y": [], "fit_x": [], "fit_y": [], "best_z": [], "best_theta": [], "label": "Live Data"}

        # Add label and textbox for optimized values
        self.optimized_z_label = QLabel("Optimized Z:")
        self.optimized_z_input = QLineEdit()
        layout.addWidget(self.optimized_z_label)
        layout.addWidget(self.optimized_z_input)

        self.optimized_theta_label = QLabel("Optimized Theta:")
        self.optimized_theta_input = QLineEdit()
        layout.addWidget(self.optimized_theta_label)
        layout.addWidget(self.optimized_theta_input)

        # Buttons for alignment
        self.align_z_button = QPushButton("Align Z")
        self.align_z_button.clicked.connect(self.align_z)
        layout.addWidget(self.align_z_button)

        self.align_theta_button = QPushButton("Align Theta")
        self.align_theta_button.clicked.connect(self.align_theta)
        layout.addWidget(self.align_theta_button)

    def update_live_plot(self):
        """Update the live plot with random data."""
        x = np.arange(len(self.data["x"]) + 1)
        y = np.random.rand(len(x))
        self.data["x"], self.data["y"] = x, y
        self.update_plot()

    def update_plot(self):
        """Update the plot with current data."""
        self.ax.clear()
        self.ax.set_title(self.data["label"])
        self.ax.set_xlabel("X-axis")
        self.ax.set_ylabel("Y-axis")
        self.ax.plot(self.data["x"], self.data["y"], "o-", label="Data")
        self.ax.plot(self.data["fit_x"], self.data["fit_y"], "r-", label="Fit")
        self.ax.legend()
        self.canvas.draw()

    def align_z(self):
        """Perform Z alignment and update the plot."""
        self.x_values = np.linspace(-1, 1, 50)
        self.y_values = error_function(self.x_values, 0, 1, 0.1) + 0.05 * np.random.normal(size=self.x_values.size)

        # Update data for the plot
        self.data["x"], self.data["y"] = self.x_values, self.y_values
        self.data["label"] = "Z-stage Alignment"
        self.current_index = 0
        
        # Timer for updating random data
        self.align_timer = QTimer(self)
        self.align_timer.timeout.connect(self.update_align_step)
        self.align_timer.start(500)  # Update every 1 second

    def update_align_step(self):
        """Update the plot for each step during Z alignment."""

        # Incrementally process data
        i = self.current_index
        if i >= len(self.x_values):
            self.align_timer.stop()  # Stop the timer when all data is processed
            # Display optimized Z
            if (self.data["best_z"] is not None) and (self.data["label"] == "Z-stage Alignment"):
                self.optimized_z_input.setText(f"{self.data['best_z']:.3f}")
            elif (self.data["best_theta"] is not None) and (self.data["label"] == "Theta-stage Alignment"):
                self.optimized_theta_input.setText(f"{self.data['best_theta']:.3f}")
            return

        # Update the data to the current step
        self.data["x"] = self.x_values[:i+1]
        self.data["y"] = self.y_values[:i+1]

        if i > 1:
            # Fit to the error function for the current data slice
            try:
                if self.data["label"] == "Z-stage Alignment":
                    popt, _ = curve_fit(error_function, self.x_values[:i+1], self.y_values[:i+1], p0=[0, 1, 0.1])
                    self.data["best_z"] = popt[0]  # Save the best Z value
                    self.x_fine_values = np.linspace(self.x_values[0], self.x_values[i], len(self.x_values) * 10)
                    self.data["fit_x"], self.data["fit_y"] = self.x_fine_values, error_function(self.x_fine_values, *popt)
                elif self.data["label"] == "Theta-stage Alignment":
                    popt, _ = curve_fit(gaussian, self.x_values[:i+1], self.y_values[:i+1], p0=[0, 1, 0.1])
                    self.data["best_theta"] = popt[0]  # Save the best Z value
                    self.x_fine_values = np.linspace(self.x_values[0], self.x_values[i], len(self.x_values) * 10)
                    self.data["fit_x"], self.data["fit_y"] = self.x_fine_values, gaussian(self.x_fine_values, *popt)
            except RuntimeError:
                pass  # Ignore fitting errors for small data points
        else:
            self.data["fit_x"], self.data["fit_y"] = [], []

        # Update the plot
        self.update_plot()

        # Move to the next data point
        self.current_index += 1

    def align_theta(self):
        """Perform Theta alignment and update the plot."""
        self.x_values = np.linspace(-1, 1, 50)
        self.y_values = gaussian(self.x_values, 0, 0.1, 1) + 0.05 * np.random.normal(size=self.x_values.size)

        # Update data for the plot
        self.data["x"], self.data["y"] = self.x_values, self.y_values
        self.data["label"] = "Theta-stage Alignment"
        self.current_index = 0
        
        # Timer for updating random data
        self.align_timer = QTimer(self)
        self.align_timer.timeout.connect(self.update_align_step)
        self.align_timer.start(500)  # Update every 1 second

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = DynamicPlot()
    main_window.show()
    sys.exit(app.exec_())

