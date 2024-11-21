import sys
import numpy as np
import pandas as pd
import epics
import time
import PyQt5.QtCore as Qt
from scipy.optimize import curve_fit
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QHBoxLayout, QCheckBox)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import QTimer

# Define the error function for Z alignment
def error_function(x, x0, scale, width):
    return scale * (1 + np.tanh((x - x0) / width)) / 2


# Define the Gaussian function for Theta alignment
def gaussian(x, x0, width, scale):
    return scale * np.exp(-((x - x0) ** 2) / (2 * width ** 2))

# Define fitting functions
def linear(x, slope, intercept):
    return slope * x + intercept

def lorentz(x, a, x0, gamma):
    return a / (1 + ((x - x0) / gamma) ** 2)


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
        self.data = {"x": [], "y": [], "label": "Live Data"}

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

        # Add checkboxes for fitting options
        self.add_fitting_options(layout)

        # Mapping checkboxes to functions
        self.function_map = {
            "Linear": linear,
            "Gaussian": gaussian,
            "Lorentz": lorentz,
            "Error function": error_function,
        }

        # Buttons for alignment
        self.scan_button = QPushButton("Scan")
        self.scan_button.clicked.connect(self.scan)
        layout.addWidget(self.scan_button)

        # Add table for scan parameters
        self.add_scan_parameters_table(layout)


    def add_scan_parameters_table(self, layout):
        # Create a table with 2 rows and 6 columns
        self.table = QTableWidget(2, 6)
        self.table.setHorizontalHeaderLabels(["Start", "Middle", "End", "Step", "Num. of Points", "Time"])
        self.table.setVerticalHeaderLabels(["Parameter 1", "Parameter 2"])

        # Initialize table with default values
        default_values = [
            ["0.000",  "5.000", "10.000", "1.000", "11", "0.500"],
            ["0.000", "10.000", "20.000", "2.000", "11", "1.000"]
        ]
        for row in range(2):
            for col in range(6):
                item = QTableWidgetItem(default_values[row][col])
                self.table.setItem(row, col, item)

        # Connect itemChanged to update dependent values
        self.table.itemChanged.connect(self.on_table_item_changed)

        # Add table to layout
        layout.addWidget(self.table)

    def on_table_item_changed(self, item):
        """Recalculate dependent values when Start, End, or Step changes."""
        # Block signals to avoid recursive triggering
        self.table.blockSignals(True)
        try:
            row = item.row()
            col = item.column()
            
            # Read the current values for calculation
            start = float(self.table.item(row, 0).text())
            middle = float(self.table.item(row, 1).text())
            end = float(self.table.item(row, 2).text())
            step = float(self.table.item(row, 3).text())
            num = int(float(self.table.item(row, 4).text()))

            
            #print(row, col, start, middle, end, step, num)
            if (col == 0) or (col == 2):  # Only recalculate scan parameters
                # Recalculate Middle
                middle = (start + end) / 2
                self.table.item(row, 0).setText(f"{start:.3f}")
                self.table.item(row, 1).setText(f"{middle:.3f}")
                self.table.item(row, 2).setText(f"{end:.3f}")
                # Recalculate step`
                step = (end - start)/(num-1)
                self.table.item(row, 3).setText(f"{step:.3f}")
            elif col == 1:
                # Recalculate End
                end =  2*middle - start
                self.table.item(row, 1).setText(f"{middle:.3f}")
                self.table.item(row, 2).setText(f"{end:.3f}")
                # Recalculate step`
                step = (end - start)/(num-1)
                self.table.item(row, 3).setText(f"{step:.3f}")
            elif col == 3:
                # Recalculate Number`
                if step != 0:
                    num = int((end - start)/step) + 1
                    self.table.item(row, 3).setText(f"{step:.3f}")
                    self.table.item(row, 4).setText(f"{num}")
                else:
                    self.table.item(row, 3).setText(f"{step:.3f}")
                    self.table.item(row, 4).setText("0")
            elif col == 4:
                if num != 0:
                    # Recalculate step`
                    step = (end - start)/(num-1)
                    self.table.item(row, 3).setText(f"{step:.3f}")
                    self.table.item(row, 4).setText(f"{num}")
                else:
                    self.table.item(row, 3).setText("0")
                    self.table.item(row, 4).setText(f"{num}")
        finally:
            # Re-enable signals after programmatic updates
            self.table.blockSignals(False) 
            

    def add_fitting_options(self, layout):
        # Create a horizontal layout for checkboxes
        fitting_layout = QHBoxLayout()
        self.checkboxes = {}

        # Label for the dropdown
        self.fitting_label = QLabel("Select a fitting function:      ")
        fitting_layout.addWidget(self.fitting_label)


        # Add checkboxes for each fitting function
        for fit_type in ["Linear", "Gaussian", "Lorentz", "Error function"]:
            checkbox = QCheckBox(fit_type)
            self.checkboxes[fit_type] = checkbox
            fitting_layout.addWidget(checkbox)

        layout.addLayout(fitting_layout)


    def load_excel_data(self):
        """Load data from an Excel file into the dropdown."""
        try:
            # Load the Excel file
            file_path = "./scan_pvs_table.xlsx"  # Replace with your Excel file path
            self.pvList = pd.read_excel(file_path)

            # Check if the column 'alias' exists
            if "Alias" in self.pvList.columns:
                # Populate the dropdown with unique values from the 'alias' column
                self.dropdown1.addItems(self.pvList[self.pvList["Type"]=="Motor"]["Alias"].dropna().unique())
                self.dropdown2.addItems(self.pvList[self.pvList["Type"]=="Detector"]["Alias"].dropna().unique())
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
        self.ax.set_xlabel("%s (%s)"  % (self.text['motor'], self.pvList.loc[self.pvList["Alias"] == self.text["motor"], "EGU"].values[0]))
        self.ax.set_ylabel("%s (%s)"  % (self.text['detector'], self.pvList.loc[self.pvList["Alias"] == self.text["detector"], "EGU"].values[0]))
        self.ax.plot(self.data["x"], self.data["y"], "o-", label="Data")
        for n in np.arange(len(self.checked_names)):
            checked_name = self.checked_names[n]
            self.ax.plot(self.data[checked_name]["fit_x"], self.data[checked_name]["fit_y"], "-", label="%s Fitting" % checked_name)
        self.ax.legend()
        self.canvas.draw()

    def scan(self):
        """Perform motor scan, record detector and update the plot."""
        # Timer for updating random data
        self.current_index = 0
        # Data for the plot
        self.data = {"x": [], "y": [], "label": self.text["motor"]}

        """List all checked checkboxes."""
        self.checked_names = [name for name, checkbox in self.checkboxes.items() if checkbox.isChecked()]
        for n in np.arange(len(self.checked_names)):
            self.data[self.checked_names[n]] = {"fit_x": [], "fit_y": [], "optimized values":[]}
        
        # Read the current values for calculation
        row = 0
        self.start = float(self.table.item(row, 0).text())
        self.middle = float(self.table.item(row, 1).text())
        self.end = float(self.table.item(row, 2).text())
        self.step = float(self.table.item(row, 3).text())
        self.num = int(float(self.table.item(row, 4).text()))
        self.accu = float(self.table.item(row, 5).text())
        self.scanPos = np.linspace(self.start, self.end, self.num)

        self.scan_timer = QTimer(self)
        self.scan_timer.timeout.connect(self.update_scan_step)
        self.scan_timer.start(500)  # Update every 1 second

    def update_scan_step(self):
        """Update the plot for each step during 1d scan."""

        # Incrementally process data
        i = self.current_index
        if i >= self.num:
            self.scan_timer.stop()  # Stop the timer when all data is processed
            # Display optimized value
            self.optimized_input.setText("%s" % [[self.checked_names[n], self.data[self.checked_names[n]]['optimized values']] for n in np.arange(len(self.checked_names))])

            return

        # Update the data to the current step
        epics.caput(self.pvList.loc[self.pvList["Alias"] == self.text["motor"], "PV"].values[0]+".VAL", self.scanPos[i]) 
        time.sleep(self.accu*0.1)
        self.data["x"] += [epics.caget(self.pvList.loc[self.pvList["Alias"] == self.text["motor"], "PV"].values[0]+".RBV")]
        # Count  detector for accumulate time
        time.sleep(self.accu)
        self.data["y"] += [epics.caget(self.pvList.loc[self.pvList["Alias"] == self.text["detector"], "PV"].values[0])]
 

        if i > 1:
            # Fit to any function for the current data slice
            try:
                for n in np.arange(len(self.checked_names)):
                    checked_name = self.checked_names[n]
                    popt, _ = curve_fit(self.function_map[checked_name], self.data['x'], self.data['y'])
                    #popt, _ = curve_fit(self.function_map[checked_name], self.data['x'], self.data['y'], p0=[0, 0.1, 1])
                    self.data[checked_name]["optimized values"] = popt  # Save the best fitting value
                    self.x_fine_values = np.linspace(self.data['x'][0], self.data['x'][-1], len(self.data['x']) * 10)
                    self.data[checked_name]["fit_x"], self.data[checked_name]["fit_y"] = self.x_fine_values, self.function_map[checked_name](self.x_fine_values, *popt)
            except RuntimeError:
                pass  # Ignore fitting errors for small data points
        else:
            self.data["fit_x"], self.data["fit_y"] = [], []

        # Update the plot
        self.update_plot()

        # Move to the next data point
        self.current_index += 1

        #print(self.data['x'])

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

