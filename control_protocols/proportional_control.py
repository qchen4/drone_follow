from .base_control import DroneControlLaw
import numpy as np

class ProportionalControl(DroneControlLaw):
    def __init__(self, Kp: float = 0.5, vmax: int = 25):
        self.Kp   = Kp
        self.vmax = vmax

    def compute_control(self, error, **_):
        err_x, err_y, *_ = error
        vx = int(np.clip(-self.Kp * err_y, -self.vmax, self.vmax))
        vy = int(np.clip(-self.Kp * err_x, -self.vmax, self.vmax))
        return vy, vx, 0, 0          # DJI RC order
