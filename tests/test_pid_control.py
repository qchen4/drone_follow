# tests/test_pid_control.py
from control_protocols.pid_control import PIDControl

def test_pid_antiwindup():
    pid = PIDControl(Kp=1, Ki=1, Kd=0, vmax=100, integral_limit=10)
    # Run many steps with same error to push the integral
    for _ in range(100):
        pid.compute_control((50, 50), dt=0.1)
    assert abs(pid.integral_x) <= 10
    assert abs(pid.integral_y) <= 10
