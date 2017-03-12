import dht
import time
import socket
import machine
import network
import ntptime
import sensors
from config import CONFIG


URL_DATA_STORE = '{host}/input/{pubkey}?private_key={privkey}&{fields}'

# Choose if DHT11 or DHT22 is used
DHT = dht.DHT22

# Micropython uses seconds since 2000 instead since 1970
UNIX_EPOCH_DELTA = 946684800


def setup_network():
    # disable access point
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    print("Disabling Access point...")
    #print(ap_if.ifconfig())

    # TODO set hostname

    # connect to WIFI as station
    print("Connecting to WIFI as client...")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(CONFIG.wifi_ssid, CONFIG.wifi_passwd)
    print("Network config:", sta_if.ifconfig())
    print("Waiting for network...")
    while sta_if.ifconfig()[0] == '0.0.0.0':
        time.sleep(0.3)
    print("Success! New network config:", sta_if.ifconfig())


def get_wifi_signal():
    """Return RSSI of used wifi."""
    if not CONFIG.enable_wifi_signal:
        return float('nan')

    sta_if = network.WLAN(network.STA_IF)
    scan = sta_if.scan()
    wifi = [wifi for wifi in scan if wifi[0].decode('ascii') == CONFIG.wifi_ssid]
    if len(wifi) != 1:
        print ("Error: scan ")
        return float('nan')
    wifi = wifi[0]

    wifi_signal = wifi[3]
    return wifi_signal


def generate_api_uri(**fields):
    fields_str = "&".join("{}={}".format(k, v) for k, v in fields.items())
    return URL_DATA_STORE.format(
        host=CONFIG.host.rstrip('/'),
        pubkey=CONFIG.api_pub_key,
        privkey=CONFIG.api_private_key,
        fields=fields_str
    )


def http_get(url):
    # from https://docs.micropython.org/en/latest/esp8266/esp8266/tutorial/network_tcp.html
    _, _, host, path = url.split('/', 3)
    if ':' in host:
        host, port = host.split(':', 2)
        port = int(port)
    else:
        port = 80
    addr = socket.getaddrinfo(host, port)[0][-1]
    s = socket.socket()
    s.connect(addr)
    s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
    answer = ''
    while True:
        data = s.recv(100)
        if data:
            answer += str(data, 'utf8')
        else:
            break
    return answer


def send_data(fields):
    for _ in range(10):
        try:
            answer = http_get(generate_api_uri(**fields))
            if (answer.startswith('HTTP/1.1 200 OK')):
                print("Sent data to server: {}".format(fields))
            else:
                raise RuntimeError(
                    "Error: Could not save Data, server "
                    "response: {}".format(answer))
        except OSError:
            print("Error: network failure (host not reached).")
        except RuntimeError as e:
            print(e)
        else:
            break
        time.sleep(3)
    else:
        print("Failed storing data, not retrying more often until next "
              "measurement.")


def good_night():
    rtc = machine.RTC()
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    rtc.alarm(rtc.ALARM0, CONFIG.update_period * 1000)


def main():
    CONFIG.read()

    # TODO this might raise, add retries
    setup_network()
    ntptime.settime()

    dht_sensor = sensors.Dht(
        CONFIG.sensor_dht_pin, CONFIG.sensor_dht_type,
        CONFIG.dht_temp_calibration, CONFIG.dht_humid_calibration)

    ds18b20_sensor = sensors.Ds18x20(CONFIG.sensor_ds18x20_pin,
                                     CONFIG.ds18b20_temp_calibration)

    while True:
        fields = {
            'temperature1': dht_sensor.temperature(),
            'temperature2': ds18b20_sensor.temperature(),
            'humidity': dht_sensor.humidity(),
            'comment': '-',
            'time': time.time() + UNIX_EPOCH_DELTA,
            'location': CONFIG.location,
            'wifi_signal': get_wifi_signal(),
            'supply_voltage': 0  # TODO   https://forum.micropython.org/viewtopic.php?t=533
        }
        print("Record:", fields)
        send_data(fields)

        if CONFIG.sleep_between_measurements:
            if machine.reset_cause() != machine.DEEPSLEEP_RESET:
                # allows easier reflashing if done in 30s after powerup
                print("Wait 30s...")
                time.sleep(30)

            # in this case while loop is useless, because after wake up it will
            # start from begin
            good_night()
        else:
            time.sleep(CONFIG.update_period)


if __name__ == '__main__':
    main()