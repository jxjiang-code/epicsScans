import time
import threading
import numpy as np
from caproto.server import pvproperty, PVGroup, ioc_arg_parser, run

class MyIOC(PVGroup):
    # Define detector PVs, only one 
    gaussian_noise = pvproperty(value=0.0, read_only=True)

    # Define motor PVs, VAL and RBV
    counting_index = pvproperty(value=0, dtype=int, name="time.VAL")
    current_time = pvproperty(value="Initializing...", dtype=str, read_only=True, max_length=30, name="time.RBV")
    # Define theta.VAL and theta.RBV
    theta_VAL = pvproperty(value=0.0, dtype=float, name="theta.VAL")
    theta_RBV = pvproperty(value=0.0, dtype=float, read_only=True, name="theta.RBV")    
    # Define z.VAL and z.RBV
    z_VAL = pvproperty(value=0.0, dtype=float, name="z.VAL")
    z_RBV = pvproperty(value=0.0, dtype=float, read_only=True, name="z.RBV")    
    @current_time.scan(period=1.0)  # Update every second
    async def current_time(self, instance, async_lib):
        """Update the current time PV."""
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        await instance.write(current_time)

    @gaussian_noise.scan(period=1.0)  # Update every second
    async def gaussian_noise(self, instance, async_lib):
        """Update the noise PV."""
        noise_value = np.random.normal(0, 1)  # Mean=0, Std=1
        await instance.write(noise_value)

    @theta_VAL.putter
    async def theta_VAL(self, instance, value):
        """When sim:theta.VAL is updated, update sim:theta.RBV with noise."""
        # Add noise to the VAL value to simulate RBV (simulated readback value)
        noise = np.random.normal(0, 0.01)  # Mean=0, Std=0.01 for small noise
        rbv_value = value + noise
        # Update the RBV PV
        await self.theta_RBV.write(rbv_value)

    @z_VAL.putter
    async def z_VAL(self, instance, value):
        """When sim:z.VAL is updated, update sim:z.RBV with noise."""
        # Add noise to the VAL value to simulate RBV (simulated readback value)
        noise = np.random.normal(0, 0.01)  # Mean=0, Std=0.01 for small noise
        rbv_value = value + noise
        # Update the RBV PV
        await self.z_RBV.write(rbv_value)

if __name__ == "__main__":
    # Parse arguments for running the IOC
    ioc_options, run_options = ioc_arg_parser(
        default_prefix="sim:",
        desc="Dummy IOC with current time, Gaussian noise and theta."
    )
    ioc = MyIOC(**ioc_options)
    run(ioc.pvdb, **run_options)

