import subprocess
import time

_MOSQUITTO_PATH = r'C:\Program Files\mosquitto'
_SERVER_CONF_PATH = '\\'.join(__file__.split('\\')[:-1])+"\\"
_ARGS = ['mosquitto.exe', '-v', '-c']


def start(echo: bool = False) -> None:
    """
    Starts both the internal and external mosquitto servers
    """
    if not echo:
        _args = [_ for _ in _ARGS if _ != '-v']
    else:
        _args = _ARGS
    _ = subprocess.Popen(_args + [_SERVER_CONF_PATH+'mosq_ext.conf'], cwd=_MOSQUITTO_PATH, shell=True)
    _ = subprocess.Popen(_args + [_SERVER_CONF_PATH+'mosq_int.conf'], cwd=_MOSQUITTO_PATH, shell=True)


def stop() -> None:
    """
    Kills all open mosquitto servers.
    """
    _ = subprocess.call(['taskkill', '/f', '/im', 'mosquitto.exe'])


if __name__ == '__main__':
    start()
    time.sleep(2)
    stop()
