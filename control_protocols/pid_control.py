# control_protocols/pid_control.py

import numpy as np
from .base_control import DroneControlLaw

class PIDControl(DroneControlLaw):
    def __init__(self, Kp=0.5, Ki=0.01, Kd=0.05, vmax=25, integral_limit=100):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.vmax = vmax

        self.integral_limit = integral_limit
        self.integral_x = 0
        self.integral_y = 0
        self.prev_error_x = 0
        self.prev_error_y = 0

    def compute_control(self, error, dt=0.07, **kwargs):
        err_x, err_y = error[:2]

        # Integral update with anti-windup
        self.integral_x = np.clip(self.integral_x + err_x * dt, -self.integral_limit, self.integral_limit)
        self.integral_y = np.clip(self.integral_y + err_y * dt, -self.integral_limit, self.integral_limit)

        # Derivative calculation
        d_err_x = (err_x - self.prev_error_x) / dt
        d_err_y = (err_y - self.prev_error_y) / dt

        # PID control calculation
        vx = int(np.clip(-self.Kp * err_y - self.Ki * self.integral_y - self.Kd * d_err_y, -self.vmax, self.vmax))
        vy = int(np.clip(-self.Kp * err_x - self.Ki * self.integral_x - self.Kd * d_err_x, -self.vmax, self.vmax))

        # Store current errors for next iteration
        self.prev_error_x = err_x
        self.prev_error_y = err_y

        return vy, vx, 0, 0
