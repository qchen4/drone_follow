import types
import numpy as np
import pytest

@pytest.fixture
def mock_tello():
    """Light-weight stub matching the few attrs your code uses."""
    stub = types.SimpleNamespace()
    stub.ax = stub.ay = stub.az = 0.0
    # add any extra attrs you read (e.g., .get_imu, .get_mission_pad_id …)
    def get_imu(): return types.SimpleNamespace(ax=0.0, ay=0.0, az=0.0)
    stub.get_imu = get_imu
    stub.send_rc_control = lambda *a, **kw: None
    stub.move          = lambda *a, **kw: None
    stub.takeoff       = lambda : None
    stub.land          = lambda : None
    return stub
