#!/usr/bin/env python
# garagedoor.py
# Controls 2 garage doors via android autoremote

import os
import signal
from time import sleep
import RPi.GPIO as GPIO
from daemon import runner
import urllib
import logging
import sys

ARKEY = ''

class GarageDaemon():
    door1 = {"switch": 7, "relay": 3, "open": False, "Id": 1}
    door2 = {"switch": 8, "relay": 5, "open": False, "Id": 2}

    log = logging.getLogger(__name__)
    logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.DEBUG)

    def __init__(self, pidfile, logfile):
        self.stdin_path = '/dev/null'
        self.stdout_path = logfile
        self.stderr_path = logfile
        self.pidfile_path = pidfile
        self.pidfile_timeout = 5

    def setup(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.door1['relay'], GPIO.OUT)
        GPIO.setup(self.door2['relay'], GPIO.OUT)
        GPIO.setup(self.door1['switch'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.door2['switch'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.output(self.door1['relay'], True)
        GPIO.output(self.door2['relay'], True)
        signal.signal(signal.SIGALRM, self.signal_handler)
        signal.signal(signal.SIGUSR1, self.signal_handler)
        signal.signal(signal.SIGUSR2, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        # Check door status every 10 seconds
        signal.setitimer(signal.ITIMER_REAL, 1, 10)

        self.log.debug("Initialization completed")

    def shutdown(self):
        self.log.debug("Shutting Down")
        signal.alarm(0)
        GPIO.cleanup()
        sys.exit(0)

    def run(self):
        self.setup()
        self.log.debug("Running")
        while True:
            signal.pause()

    def signal_handler(self, sigval, frame):
        if sigval == signal.SIGALRM:
            self.checkDoorStatus()
        elif sigval == signal.SIGTERM:
            self.shutdown()
        elif sigval == signal.SIGUSR1:
            self.activateDoor(self.door1['relay'])
        elif sigval == signal.SIGUSR2:
            self.activateDoor(self.door2['relay'])
        return

    def checkDoorStatus(self):
        
        # Genie switches ground when active
        for door in [self.door1, self.door2]:
            o_val = GPIO.input(door['switch'])

            if o_val:
                # Door Open
                if not door['open']:
                    door['open'] = True
                    self.log.debug("Door " + str(door['Id']) + " open")
                    self.sendMessage(str(door['Id']) + "=:=open")
            else:
                # Closeswitch active
                if door['open']:
                    door['open'] = False
                    self.log.debug("Door " + str(door['Id']) + " closed")
                    self.sendMessage(str(door['Id']) + "=:=closed")

    def activateDoor(self, doorPin):

        if doorPin == self.door1['relay']:
            if self.door1['open']:
                self.log.debug("Closing door 1")
            else:
                self.log.debug("Opening door 1")
        elif doorPin == self.door2['relay']:
            if self.door2['open']:
                self.log.debug("Closing door 2")
            else:
                self.log.debug("Opening door 2")

        GPIO.output(doorPin, False)
        sleep(.5)
        GPIO.output(doorPin, True)

    def sendMessage(self, message):
        msg = "Garage " + message
        self.log.debug("Sending message: " + msg)
        try:
            retval = urllib.urlopen('http://autoremotejoaomgcd.appspot.com/sendmessage?key=' + ARKEY + '&message=' + msg)
            if retval.getcode() != 200:
                self.log.debug(str(retval.getcode()) + ": AR error sending message")
                self.log.debug(retval.readlines())
        except IOError:
            self.log.debug("Error sending HTTP message")

appDir = os.path.dirname(os.path.realpath(__file__))
logfile = os.path.join(appDir, 'garage.log')
pidfile = os.path.join(appDir, 'garage.pid')


if __name__ == '__main__':

    app = GarageDaemon(pidfile, logfile)
    daemon_runner = runner.DaemonRunner(app)
    daemon_runner.do_action()
