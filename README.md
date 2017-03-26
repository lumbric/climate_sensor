Record temperature and humidity using Micropython and send data to a remote
logging service via HTTP/GET.

Supported sensors:
 * DHT11
 * DHT22
 * DS18B20
 
Supported logging services:
* thingspeak
* phant / data.sparkfun.com
* arbitrary HTTP API via configuration

Tested only using [Wemos D1 mini ESP8266](https://www.wemos.cc/product/d1-mini.html), but should be easily portable for similar hardware.

Install
-------
Install [micropython](http://micropython.org/) firmware, copy all *.py files (e.g. using [mpfshell](https://github.com/wendlers/mpfshell)) and configure as described below.


Configuration
-------------
To create a config.json file run on [MicroPython REPL prompt (e.g via piccoom)](https://docs.micropython.org/en/latest/esp8266/esp8266/tutorial/repl.html#getting-a-micropython-repl-prompt):

```
import config
config.setup()
```

To rewrite the configuration file, reset the ESP8266, interrupt the running main.py by CTRL+C and
then follow above instructions.
