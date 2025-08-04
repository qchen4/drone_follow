# landing_protocols/simple_landing.py

import logging
from .base_landing import LandingProtocolBase

class SimpleLanding(LandingProtocolBase):
    """Simple landing protocol that directly lands the drone."""
    
    def land(self, tello, **kwargs):
        """Execute simple landing by directly calling tello.land()."""
        logging.info("Executing simple landing protocol.")
        try:
            # Stop all movement
            tello.send_rc_control(0, 0, 0, 0)
            logging.info("Drone landed successfully.")
            tello.land()
        except Exception as e:
            logging.error(f"Error during simple landing: {e}")
            # Force land even if there's an error
            try:
                tello.land()
            except:
                pass
