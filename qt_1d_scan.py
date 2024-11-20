import sys
import numpy as np
import pandas as pd
import time
from scipy.optimize import curve_fit
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QHBoxLayout)
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

        # Label for the dropdown
        self.label1 = QLabel("Select a motor from the dropdown:")
        layout.addWidget(self.label1)

        # Create the dropdown (QComboBox)
        self.dropdown1 = QComboBox()
        layout.addWidget(self.dropdown1)

        # Label for the dropdown
        self.label2 = QLabel("Select a detector from the dropdown:")
        layout.addWidget(self.label2)

        # Create the dropdown (QComboBox)
        self.dropdown2 = QComboBox()
        layout.addWidget(self.dropdown2)

        # Load data into the dropdown
        self.load_excel_data()

        # Connect dropdown selection change to a method
        self.dropdown1.currentTextChanged.connect(self.on_dropdown1_change)
        self.dropdown2.currentTextChanged.connect(self.on_dropdown2_change)

        
        # Add label and textbox for optimized values
        self.optimized_label = QLabel("Optimized %s:" % self.dropdown1.itemText(0))
        self.text = {"motor": self.dropdown1.itemText(0), "detector": self.dropdown2.itemText(0)}
        self.data["label"] = self.dropdown1.itemText(0)
        self.optimized_input = QLineEdit()
        layout.addWidget(self.optimized_label)
        layout.addWidget(self.optimized_input)


        # Buttons for alignment
        self.scan_button = QPushButton("Scan")
        self.scan_button.clicked.connect(self.scan)
        layout.addWidget(self.scan_button)

        # Add table for scan parameters
        self.add_scan_parameters_table(layout)

    def add_scan_parameters_table(self, layout):
        # Create a table with 2 rows and 6 columns
        self.table = QTableWidget(2, 6)
        self.table.setHorizontalHeaderLabels(["Start", "Middle", "End", "Step", "Time", "Num. of Points"])
        self.table.setVerticalHeaderLabels(["Parameter 1", "Parameter 2"])

        # Initialize table with default values
        default_values = [
            ["0", "5", "10", "1", "0.5", "10"],
            ["0", "10", "20", "2", "1.0","10"]
        ]
        for row in range(2):
            for col in range(6):
                self.table.setItem(row, col, QTableWidgetItem(default_values[row][col]))

        # Add table to layout
        layout.addWidget(self.table)

    def load_excel_data(self):
        """Load data from an Excel file into the dropdown."""
        try:
            # Load the Excel file
            file_path = "./scan_pvs_table.xlsx"  # Replace with your Excel file path
            data = pd.read_excel(file_path)

            # Check if the column 'alias' exists
            if "Alias" in data.columns:
                # Populate the dropdown with unique values from the 'alias' column
                self.dropdown1.addItems(data[data["Type"]=="Motor"]["Alias"].dropna().unique())
                self.dropdown2.addItems(data[data["Type"]=="Detector"]["Alias"].dropna().unique())
            else:
                self.label1.setText("Column 'alias' not found in the Excel file.")
                self.label2.setText("Column 'alias' not found in the Excel file.")
        except Exception as e:
            self.label1.setText(f"Error loading Excel file: {e}")
            self.label2.setText(f"Error loading Excel file: {e}")

    def on_dropdown1_change(self, text):
        """Handle the dropdown selection change."""
        self.label1.setText(f"Selected motor: {text}")
        self.optimized_label.setText(f"Optimized {text}:" )
        self.text["motor"] = text
    def on_dropdown2_change(self, text):
        self.label2.setText(f"Selected detector: {text}")
        self.text["detector"] = text

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

    def scan(self):
        """Perform motor scan, record detector and update the plot."""
        # Timer for updating random data
        self.current_index = 0
        self.scan_timer = QTimer(self)
        self.scan_timer.timeout.connect(self.update_scan_step)
        self.scan_timer.start(500)  # Update every 1 second

    def update_scan_step(self):
        """Update the plot for each step during 1d scan."""

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
        epics.caput(data.loc[data["Alias"] == self.text["motor"], "PV"].values[0]+".VAL") 
        self.data["x"] += epics.caget(data.loc[data["Alias"] == self.text["motor"], "PV"].values[0]+".RBV") 
        self.data["y"] += epics.caget(data.loc[data["Alias"] == self.text["detector"], "PV"].values[0]) 
 

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

