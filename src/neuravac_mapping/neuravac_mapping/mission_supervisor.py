"""Mission transitions only; callers must enforce safety and command stops.

This module does not operate hardware or determine whether a goal is reachable.
"""
import math


class MissionSupervisor:
    def __init__(self):
        self.state = 'idle'
        self.reason = ''
        self.return_goal = None

    def start(self, return_goal, ready):
        if self.state in ('exploring', 'returning'):
            raise ValueError('Mission already active')
        if not ready:
            raise ValueError('Robot is not ready')
        try:
            x, y = return_goal
            valid = all(isinstance(v, (int, float)) and not isinstance(v, bool)
                        and math.isfinite(v) for v in (x, y))
        except (TypeError, ValueError):
            valid = False
        if not valid:
            raise ValueError('Return goal must contain two finite coordinates')
        self.return_goal = (float(x), float(y))
        self.reason = ''
        self.state = 'exploring'

    def exploration_finished(self):
        if self.state == 'exploring':
            self.state = 'returning'

    def request_return(self):
        self.exploration_finished()

    def return_finished(self, success):
        if self.state != 'returning':
            return
        if success:
            self.state = 'complete'
            self.reason = 'Returned to selected spot'
        else:
            self.state = 'stopped'
            self.reason = 'Return spot unreachable; waiting for operator'

    def hazard(self, reason):
        if self.state in ('exploring', 'returning'):
            self.state = 'stopped'
            self.reason = reason
