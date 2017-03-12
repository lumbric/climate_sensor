import os
import json


def file_exists(filename):
    # os.path not shipped with micropython core
    try:
        os.stat(filename)
    except OSError:
        exists = False
    else:
        exists = True
    return exists


def _bool(val):
    if isinstance(val, str):
        return val.lower in ('0', 'false', 'f')
    return bool(val)


def _callable(val):
    return eval("lambda x: {}".format(val))


def setup():
    CONFIG.input()


class Config(object):
    def __init__(self, keys, types, descriptions, defaults,
                 filename='config.json'):
        assert len(keys) == len(types), "keys and types must be of same length"
        self._data = {}
        self._keys = keys
        self._descriptions = descriptions
        self._types = dict(zip(keys, types))
        self._defaults = dict(zip(keys, defaults))
        self.filename = filename

    def __getattr__(self, key):
        return self._types[key](self._data[key])

    def input(self):
        """Ask user for values for each key via STDOUT/STDIN. Default values
        will be either provdied default values or values from previous config
        file."""
        defaults = self._defaults
        if file_exists(self.filename):
            while True:
                overwrite = input("File exists. Overwrite? [y/n] ")
                if overwrite.lower() in ('y', 'yes'):
                    break
                if overwrite.lower() in ('n', 'no'):
                    return
            old_as_default = input("Defaults from old file? [Y/n] ")
            if old_as_default.lower() in ('y', 'yes', ''):
                data = self._read()
                defaults = {key: data.get(key, self._defaults[key])
                            for key in self._keys}

        self._data = {}
        for key, description in zip(self._keys, self._descriptions):
            default = defaults[key]
            if description:
                print("\n{}".format(description))
            default_s = " [{}]".format(default) if default is not None else ''
            value = input("  {}{}: ".format(key, default_s))
            if value == '' and default is not None:
                value = default
            # only for checking that it can be converted...
            self._types[key](value)
            self._data[key] = value
        self.write()

    def write(self):
        """Write current values to file. Any existing file will be
        overwritten."""
        data_json = json.dumps(self._data)
        with open(self.filename, 'w') as f:
            f.write(data_json)

    def _read(self):
        if not file_exists(self.filename):
            raise ValueError("{} not found. Run 'import config; config.setup()'"
                             "to generate config.".format(self.filename))
        with open(self.filename, 'r') as f:
            data = json.load(f)
        return data

    def read(self):
        data = self._read()
        self._check_schema(data)
        self._data = data

    def _check_schema(self, data):
        # TODO check types? how? (types contains callables, not types...)
        if not isinstance(data, dict):
            raise ValueError("invalid config type {}".format(type(data)))
        if set(self._keys) != set(data.keys()):
            raise ValueError("invalid config keys (missing: {}, undefined: "
                             "{})".format(
                                 set(self._keys) - set(data.keys()),
                                 set(data.keys()) - set(self._keys),
                             ))

    def check_schema(self):
        # empty config might not fulfill schema specs
        self._check_schema(self._data)


CONFIG_DATA = (
    ('sensor_dht_pin', int, 'Pin for data to DHT chip, use -1 to disable', 2),
    ('sensor_dht_type', str, 'Type of DHT sensory - either "DHT11" (blue) or "DHT22" (white)', 'DHT11'),
    ('sensor_ds18x20_pin', int, 'Pin for data to ds18b20 chip, use -1 to disable', -1),
    ('update_period', int, 'update interval for measurements in seconds', 10 * 60),
    ('enable_wifi_signal', _bool, "Scanning wifi might eat the batteryfaster, "
                                  "but we can do funny statistics (relation "
                                  "between humidity and wifi signal) ", True),
    ('sleep_between_measurements', _bool, "go to deep sleep between "
                                          "measurements to safe power "
                                          "<1mA instead of 75mA", True),
    ('location', str, 'Where is the sensore located?', '-'),
    ('api_pub_key', str, 'Public API key', None),
    ('api_private_key', str, 'Private API key', None),
    ('host', str, 'Host and port for phant server (something like http://HOST:PORT/ or https://HOST/ or so)', 'http://m33x7:8888/'),
    ('wifi_ssid', str, 'WIFI SSID', None),
    ('wifi_passwd', str, 'WIFI password', None),
    ('dht_temp_calibration', _callable, 'Temperatur calibration', 'x'),
    ('dht_humid_calibration', _callable, 'Humidity calibration', 'x'),
    ('ds18b20_temp_calibration', _callable, 'Temperatur calibration', 'x'),
)
CONFIG = Config(*zip(*CONFIG_DATA))
