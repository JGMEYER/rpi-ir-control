from gpiozero import InputDevice, LED

ir_receiver = InputDevice(16, pull_up=True)
led_red = LED(26)

while 1:
    if ir_receiver.is_active:
        led_red.on()
    else:
        led_red.off()
