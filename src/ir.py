import time

from gpiozero import InputDevice, LED


class IR_Receiver():
    """
    IR Receiver

    Contains helpful functions for decoding IR signals from a physical IR
    Receiver.
    """

    # maximum pulse length that counts as a read
    MAX_READ_PULSE = 65 * 0.001

    # timing resolution for pulse reads
    PULSE_RESOLUTION = 10 * 0.000001

    def __init__(self):
        self.sensor = InputDevice(16)
        self.led = LED(26)

    def read_loop(self):
        print("Reading IR inputs")
        pulses = []

        def track_pulse(pulse, is_high):
            nonlocal pulses
            if pulse != 0:
                pulses.append((pulse * 100000, is_high))
            else:
                # occasionally we'll get rogue pulses. ignore these
                if len(pulses) > 2:
                    if self._pulses_match_protocol(pulses):
                        self._print_pulses(pulses)
                        print(self._pulses_to_binary(pulses))
                pulses = []

        while 1:
            high_pulse = self._sense_pulse(False)
            track_pulse(high_pulse, False)
            low_pulse = self._sense_pulse(True)
            track_pulse(low_pulse, True)

    def _sense_pulse(self, active):
        pulse = 0
        while self.sensor.is_active is active:
            # pulse has timed out, return nothing
            if pulse >= self.MAX_READ_PULSE:
                return 0
            self.led.on() if not active else self.led.off()
            pulse += self.PULSE_RESOLUTION
            time.sleep(self.PULSE_RESOLUTION)
        return pulse

    def _print_pulses(self, pulses):
        print("{0:10} {1:10}".format("OFF (1)", "ON (0)"))
        for idx in range(0, len(pulses), 2):
            print("{0:7.2f} usecs {1:7.2f} usecs".format(pulses[idx][0],
                                                         pulses[idx+1][0]))

    def _pulses_match_protocol(self, pulses):
        if pulses[0][1] is not True:
            print("Pulses does not start with a LOW pulse")
            return False
        if len(pulses) % 2 != 0:
            print("Pulses does not have matching pairs of (LOW, HIGH) pulses")
            return False
        # range is arbitrary based on results I've seen that *seem* correct
        if len(pulses) - 3 != len([pulse for pulse, is_high in pulses[3:]
                                   if 2.99 <= pulse <= 17]):
            print("One or more pulses does not fit in the expected range")
            return False
        return True

    def _pulses_to_binary(self, pulses):
        pulse_bin = ""
        # ignore first and last pulse, then read in pairs
        for idx in range(1, len(pulses)-1, 2):
            if pulses[idx+1][0] / pulses[idx][0] >= 2:
                pulse_bin += "1"
            else:
                pulse_bin += "0"
        return pulse_bin


if __name__ == "__main__":
    IR_Receiver().read_loop()
