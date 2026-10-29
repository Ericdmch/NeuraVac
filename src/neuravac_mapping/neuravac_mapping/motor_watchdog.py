"""Latch a motion lease closed after loss of command, safety, or ownership.

The serial owner must call check periodically and send a physical stop on a
false result. This object alone cannot stop a motor or survive driver failure.
"""
import math


class MotorWatchdog:
    def __init__(self, timeout=.3):
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('Watchdog timeout must be positive')
        self.timeout = timeout
        self.armed = False
        self.last = None
        self.reason = 'not armed'

    def arm(self, now):
        if not math.isfinite(now):
            raise ValueError('Invalid time')
        self.armed = True
        self.last = now
        self.reason = ''

    def preempt(self, reason):
        self.armed = False
        self.reason = reason

    def check(self, now, safe, reason='safety data unavailable'):
        if not self.armed:
            return False
        if not math.isfinite(now) or now < self.last or now - self.last > self.timeout:
            self.preempt('autonomous command timeout')
        elif safe is not True:
            self.preempt(reason)
        return self.armed

    def heartbeat(self, now, safe, reason='safety data unavailable'):
        if not self.check(now, safe, reason):
            return False
        self.last = now
        return True
