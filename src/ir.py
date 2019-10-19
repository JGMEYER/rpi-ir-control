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
    PULSE_RESOLUTION = 5 * 0.000001

    def __init__(self):
        self.sensor = InputDevice(16, pull_up=True)
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
                    self._print_pulses(pulses)
                pulses = []

        while 1:
            high_pulse = self._sense_pulse(True)
            track_pulse(high_pulse, True)
            low_pulse = self._sense_pulse(False)
            track_pulse(low_pulse, False)

    def _sense_pulse(self, active):
        pulse = 0
        while self.sensor.is_active == active:
            # pulse has timed out, return nothing
            if pulse >= self.MAX_READ_PULSE:
                return 0
            self.led.on() if active else self.led.off()
            pulse += self.PULSE_RESOLUTION
            time.sleep(self.PULSE_RESOLUTION)
        return pulse

    def _print_pulses(self, pulses):
        if pulses[0][1] is not False:
            print("Pulses does not start with a LOW pulse")
            return
        if len(pulses) % 2 != 0:
            print("Pulses does not have matching pairs of (LOW, HIGH) pulses")
            return

        print("{0:10} {1:10}".format("OFF", "ON"))
        for idx in range(0, len(pulses), 2):
            print("{0:7.2f} usecs {1:7.2f} usecs".format(pulses[idx][0],
                                                         pulses[idx+1][0]))


if __name__ == "__main__":
    IR_Receiver().read_loop()
