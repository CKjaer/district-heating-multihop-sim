import numpy as np
from config.models import Radio, UndergroundPropagation

_PERMEABILITY_VACUUM = 1.257e-6 
_PERMITTIVITY_VACUUM = 8.854e-12
_NEPER2DB = 8.686

class LogDistance:
    """Calculates the log-distance path loss in dB"""
    def __init__(self, radio: Radio, loss_exponent=2.0, ref_dist=1.0):
        self.f = radio.frequency # Hz
        self.gamma = loss_exponent
        self.d0 = ref_dist       # m
        self.K = (
            - radio.rx_gain 
            - radio.tx_gain 
            + 20 * np.log10(self.f) 
            + 20 * np.log10(self.d0) 
            - 147.55 )

    def __call__(self, dist):
        return self.K + 10 * self.gamma * np.log10(dist / self.d0) 

class MaterialAttenuation:
    """Calculates the attenuation in lossy materials from the complex propagation constant in dB"""
    def __init__(self, radio: Radio, u2u: UndergroundPropagation):
        epsilon = _PERMITTIVITY_VACUUM * u2u.rel_permittivity * (1 - 1j * np.tan(u2u.loss_tan))
        mu = _PERMEABILITY_VACUUM * u2u.rel_permeability
        gamma = 1j * 2 * np.pi * radio.frequency * np.sqrt(mu * epsilon)                 
        self.alpha =  np.real(gamma) * _NEPER2DB # dB/m
        self.beta = np.imag(gamma) # rad/m

    def __call__(self, dist):
        return self.alpha * dist