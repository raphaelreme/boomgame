"""Timers in the model"""


class Timer:
    """Timer that keep track of the time

    Basic usage:
    ```
    timer = Timer()
    timer.start(10.5)
    for i in range(15):
        done = timer.update(1.)
        if done:
            break
    assert i == 10
    ```

    Attrs:
        increase (bool): If True, the current value increase up to the total one
                        If False, the current value deacrease from the total one (to 0)
        is_active (bool): True if the timer has been started
        is_done (bool): True when an active timer has reached the total value
        total (float): Total time to wait
        current (float): Either the time left (decrease mode), or time elapsed (increase mode)
    """

    def __init__(self, increase: bool = True) -> None:
        self.increase = increase
        self.is_active = False
        self.total = 0.0
        self.current = 0.0

    @property
    def is_done(self) -> bool:
        if not self.is_active:
            return False

        return self.increase and self.current >= self.total or not self.increase and self.current <= 0

    def start(self, total: float) -> None:
        """Start the timer with `total` time

        Cannot be started if already active (Call reset first)

        Args:
            total (float): Time to wait for this run
        """
        if self.is_active:
            raise RuntimeError("Timer already active")

        self.is_active = True

        self.total = total
        if self.increase:
            self.current = 0.0
        else:
            self.current = self.total

    def update(self, delay: float) -> bool:
        """Update the timer by a delay

        Does nothing if not active

        Args:
            delay (float): Time elapsed

        Returns:
            bool: True if the timer is done
        """
        if not self.is_active:
            return False

        if self.increase:
            self.current += delay
            return self.current >= self.total

        self.current -= delay
        return self.current <= 0

    def reset(self) -> None:
        """Reset the time

        The timer is no longer active and can be restarted. Can be called even if not done.
        """
        self.is_active = False
