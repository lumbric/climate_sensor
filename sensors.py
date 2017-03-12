import dht
import time
import onewire
import ds18x20
from machine import Pin


class Dht:
    def __init__(self, pin_nr, sensor_type='DHT11', temp_calibration=None,
                 humid_calibration=None):
        assert sensor_type in ('DHT11', 'DHT22'), "invalid sensor_type"
        self._temp_calibration = temp_calibration \
            if temp_calibration is not None else lambda x: x
        self._humid_calibration = humid_calibration \
            if humid_calibration is not None else lambda x: x

        dht_cls = getattr(dht, sensor_type)
        self._sensor = None
        if pin_nr >= 0:
            self._sensor = dht_cls(Pin(pin_nr, Pin.IN, Pin.PULL_UP))

        self._measured = False

    def _measure(self):
        # measure every 2 calls, i.e. after calling temperature() and humidity()
        if not self._measured and self._sensor:

            self._sensor.measure()
            # TODO in case of exception loop...
            #print("DHT measurement failed: ", e)
            #time.sleep(2)
        self._measured = not self._measured

    def temperature(self):
        if not self._sensor:
            return float('nan')

        self._measure()
        return self._temp_calibration(self._sensor.temperature())

    def humidity(self):
        if not self._sensor:
            return float('nan')

        self._measure()
        return self._humid_calibration(self._sensor.humidity())


class Ds18x20:
    def __init__(self, pin_nr, calibration=None):
        if calibration is not None:
            self._calibration = calibration
        else:
            self._calibration = lambda x: x

        self._sensor = None
        if pin_nr >= 0:
            ow = onewire.OneWire(Pin(pin_nr, Pin.IN, Pin.PULL_UP))
            self._sensor = ds18x20.DS18X20(ow)

    def temperature(self):
        if not self._sensor:
            return float('nan')
        roms = self._sensor.scan()
        self._sensor.convert_temp()
        time.sleep_ms(750)
        for rom in roms:
            return self._calibration(self._sensor.read_temp(rom))
        else:
            return float('nan')
