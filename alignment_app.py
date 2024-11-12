from pywebio import start_server
from pywebio.output import put_text, put_row, put_buttons, put_scope, use_scope, clear_scope, put_table, put_html
from pywebio.input import input, FLOAT
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from io import BytesIO
import base64

# Simulate an error function for z alignment
def error_function(z, z0, A, B):
    return A * 0.5 * (1 + np.tanh((z - z0) / B))

# Simulate a Gaussian for theta alignment
def gaussian(x, x0, sigma, amplitude):
    return amplitude * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2))

# Plotting helper to generate base64-encoded images
def plot_function(x, y, fit_func, fit_params, title):
    plt.figure()
    plt.plot(x, y, 'o', label="Data")
    plt.plot(x, fit_func(x, *fit_params), '-', label="Fit")
    plt.xlabel("Position")
    plt.ylabel("Intensity")
    plt.title(title)
    plt.legend()
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    img_str = base64.b64encode(buffer.read()).decode("utf-8")
    plt.close()
    return img_str

# Main function for PyWebIO app
def align_sample():
    put_text("Grazing Incidence X-Ray Diffraction Sample Alignment")
    put_scope("plot_scope")

    
    # Simulate z alignment
    def align_z():
        z_values = np.linspace(-1, 1, 50)
        intensity_values = error_function(z_values, 0, 1, 0.1) + 0.05 * np.random.normal(size=z_values.size)
        
        # Fit to an error function
        popt, _ = curve_fit(error_function, z_values, intensity_values, p0=[0, 1, 0.1])
        best_z = popt[0]
        
        # Plot
        img_str = plot_function(z_values, intensity_values, error_function, popt, "z-stage Alignment")
        with use_scope("plot_scope", clear=True):
            put_text("Aligning z-stage...")
            put_html(f'<img src="data:image/png;base64,{img_str}" style="width:70%;"/>')
        
        return best_z
    
    # Simulate theta alignment
    def align_theta():
        theta_values = np.linspace(-1, 1, 50)
        intensity_values = gaussian(theta_values, 0, 0.1, 1) + 0.05 * np.random.normal(size=theta_values.size)
        
        # Fit to a Gaussian
        popt, _ = curve_fit(gaussian, theta_values, intensity_values, p0=[0, 0.1, 1])
        best_theta = popt[0]
        
        # Plot
        img_str = plot_function(theta_values, intensity_values, gaussian, popt, "Theta Alignment")
        with use_scope("plot_scope", clear=True):
            put_text("Aligning theta...")
            put_html(f'<img src="data:image/png;base64,{img_str}" style="width:70%;"/>')
        
        return best_theta

    # Control buttons for z and theta alignment
    put_row([
        put_buttons(['Align z'], onclick=[lambda: align_z()]),
        put_buttons(['Align theta'], onclick=[lambda: align_theta()])
    ])

# Start PyWebIO server
if __name__ == "__main__":
    start_server(align_sample, port=8080)

