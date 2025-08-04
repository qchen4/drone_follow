from .base_control import DroneControlLaw
import numpy as np

class PIControl(DroneControlLaw):
    def __init__(self, Kp=0.5, Ki=0.01, vmax=25):
        self.Kp, self.Ki, self.vmax = Kp, Ki, vmax
        self.int_x = self.int_y = 0

    def compute_control(self, error, dt=0.07, **_):
        err_x, err_y, *_ = error
        self.int_x += err_x * dt
        self.int_y += err_y * dt
        vx = int(np.clip(-self.Kp * err_y - self.Ki * self.int_y, -self.vmax, self.vmax))
        vy = int(np.clip(-self.Kp * err_x - self.Ki * self.int_x, -self.vmax, self.vmax))
        return vy, vx, 0, 0
