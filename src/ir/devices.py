import logging
import time
from datetime import datetime
from typing import List

from gpiozero import InputDevice, LED

FORMAT = '%(asctime)-15s [%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
log = logging.getLogger(__name__)

class Pulse():
    """
    Pulse

    A pulse read from the IR Receiver as defined by the NEC Infrared
    Transmission Protocol.

    More information on the NEC Infrared Transmission Protocol can be found at:
    https://techdocs.altium.com/display/FPGA/NEC+Infrared+Transmission+Protocol

    Parameters
        length:    pulse length in seconds
        is_space:  the pulse marks a space (1 on IR Receiver)
                   as opposed to a burst (0 on IR Receiver)
    """
    # small gap as defined by the NEC Infrared Transmission Protocol
    NEC_SMALL_GAP = 562.5 * 0.000001  # sec

    # large gap as defined by the NEC Infrared Transmission Protocol
    NEC_LARGE_GAP = 1687.5 * 0.000001  # sec

    # tolerance for detecting an NEC gap - arbitrary
    GAP_TOLERANCE = 270 * 0.000001  # sec

    def __init__(self, length, is_space):
        self.length = length
        self.is_space = is_space

    def __str__(self):
        return f"{int(self.is_space)} {int(self.length * 1000000)} usecs"

    def is_small_gap(self):
        min = self.NEC_SMALL_GAP - self.GAP_TOLERANCE
        max = self.NEC_SMALL_GAP + self.GAP_TOLERANCE
        return min <= self.length <= max

    def is_large_gap(self):
        min = self.NEC_LARGE_GAP - self.GAP_TOLERANCE
        max = self.NEC_LARGE_GAP + self.GAP_TOLERANCE
        return min <= self.length <= max


class IR_Receiver():
    """
    IR Receiver

    Contains helpful functions for decoding IR signals from a physical IR
    Receiver.

    IR Receivers signal 1 by default when no IR signal is detected, and 0
    otherwise. So a HIGH pulse is 0, while a LOW pulse is 1.

    More information on the NEC Infrared Transmission Protocol can be found at:
    https://techdocs.altium.com/display/FPGA/NEC+Infrared+Transmission+Protocol
    """

    # minimum pulse length that counts as a read - arbitrary
    MIN_PULSE_READ = 50 * 0.000001  # sec

    # maximum pulse length that counts as a read - arbitrary
    MAX_PULSE_READ = 65000 * 0.000001  # sec

    def __init__(self):
        self.sensor = InputDevice(16)
        self.led = LED(26)

    def read_loop(self):
        """
        Continuously reads IR pulses and decodes them into NEC compliant
        messages.
        """
        log.info("Reading IR inputs")

        pulses: List[Pulse] = []

        def track_pulse(pulse):
            nonlocal pulses
            if pulse and \
               self.MIN_PULSE_READ < pulse.length < self.MAX_PULSE_READ:
                log.debug(pulse)
                pulses.append(pulse)
            elif len(pulses) > 0:
                message = None
                try:
                    message = self._pulses_to_binary_message(pulses)
                except ValueError as e:
                    log.error(e, exc_info=True)
                finally:
                    if message:
                        log.info(hex(message))
                pulses = []

        while 1:
            # empty space (registers as 1 on IR Receiver)
            space_pulse = self._sense_pulse(True)
            track_pulse(space_pulse)
            # burst pulse (registers as 0 on IR Receiver)
            burst_pulse = self._sense_pulse(False)
            track_pulse(burst_pulse)

    def _sense_pulse(self, is_space):
        """Listens for a pulse space or burst."""
        start = datetime.now()
        while self.sensor.is_active is is_space:
            # timed out, return nothing
            if (datetime.now() - start).total_seconds() >= self.MAX_PULSE_READ:
                return None
            self.led.off() if is_space else self.led.on()
        return Pulse((datetime.now() - start).total_seconds(), is_space)

    def _sanitize_pulses(self, pulses):
        """
        Confirms pulses received match expected pattern and removes preceding
        pulses not relevant to the message, i.e. [<arbitrary space>,
        9ms leading pulse burst, 4.5ms space], as well as trailing burst.
        """
        if pulses[0].is_space is not True:
            raise ValueError("Pulse patterns must begin with a space")
        if len(pulses) != 68:
            raise ValueError(f"Pulse patterns must be 68 pulses long (1 space "
                             f"+ 1 9ms burst + 1 4.5ms space + 64 message "
                             f"pulses + 1 trailing burst). Received: "
                             f"{len(pulses)}")
        for idx in range(0, len(pulses), 2):
            if not (pulses[idx].is_space is True and
                    pulses[idx+1].is_space is False):
                raise ValueError(f"Pulse pattern does not alternate between "
                                 f"spaces and bursts beginning at index {idx}")

        # remove all pulses not relevant to encoded message
        pulses = pulses[3:-1]

        for idx in range(0, len(pulses), 2):  # bursts
            if not pulses[idx].is_small_gap():
                raise ValueError(f"Burst at index {idx} does not match NEC"
                                 f"specifications ({pulses[idx]})")
        for idx in range(1, len(pulses), 2):  # spaces
            if not (pulses[idx].is_small_gap() or pulses[idx].is_large_gap()):
                raise ValueError(f"Space at index {idx} does not match NEC "
                                 f"specifications ({pulses[idx]})")
        return pulses

    def _pulses_to_binary_message(self, pulses):
        """Converts sequence of pulses into NEC compliant binary message."""
        try:
            pulses = self._sanitize_pulses(pulses)
        except ValueError as e:
            log.error(e)
            return None

        msg_str = ""
        # use size of spaces to determine encoded message values
        for idx in range(1, len(pulses), 2):
            if pulses[idx].is_small_gap():
                msg_str += "0"
            elif pulses[idx].is_large_gap():
                msg_str += "1"
            else:
                raise ValueError(f"Pulse pattern malformed")

        msg_bin = int(msg_str, 2)

        # validate address and command
        address = msg_bin & 0xFF000000 >> (6 * 4)
        address_inverse = msg_bin & 0x00FF0000 >> (4 * 4)
        command = msg_bin & 0x0000FF00 >> (2 * 4)
        command_inverse = msg_bin & 0x000000FF
        if command == ~command_inverse:
            raise ValueError(f"Address does not match inverse ({hex(address)} "
                             f"{hex(address_inverse)})")
        if command == ~command_inverse:
            raise ValueError(f"Command does not match inverse ({hex(command)} "
                             f"{hex(command_inverse)})")

        return msg_bin


if __name__ == "__main__":
    IR_Receiver().read_loop()
