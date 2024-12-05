# Dynamic Plot and One-Dimensional Scan Application

This project provides a Python-based GUI application for dynamic plotting and performing one-dimensional scans, designed for scientific data analysis and visualization. It incorporates tools for real-time data updates, crosshair positioning, function fitting, and user-configurable scan parameters.

## Features

- **Dynamic Plotting**:
  - Real-time updates of plotted data.
  - Crosshair positioning for detailed analysis.

- **Scan Configuration**:
  - User-configurable scan parameters via a table interface.
  - Options to select motors and detectors from dropdown menus.

- **Function Fitting**:
  - Supports fitting with the following functions:
    - Linear
    - Gaussian
    - Lorentzian
    - Error function (tanh-based).

- **Graphical User Interface**:
  - Built with PyQt5.
  - Interactive and intuitive layout.
  - Matplotlib integration for data visualization.

## Requirements

- Python 3.8+
- Libraries:
  - `numpy`
  - `pandas`
  - `matplotlib`
  - `PyQt5`
  - `scipy`
  - `openpyxl`
  - `epics`

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/jxjiang-code/epicsScans.git
   cd epicsScans
