from enum import IntFlag


class SoundbarCode(IntFlag):
    """Vizio Soundbar Remote IR Codes"""
    POWER_TOGGLE = 0x00ff02fd
    VOLUME_UP = 0x00ff827d
    VOLUME_DOWN = 0x00ffa25d
    MUTE_TOGGLE = 0x00ff12ed


class TVCode(IntFlag):
    """LG TV Remote IR Codes"""
    POWER_TOGGLE = 0x20df10ef
    VOLUME_UP = 0x20df40bf
    VOLUME_DOWN = 0x20dfc03f
    MUTE_TOGGLE = 0x20df906f
