from typing import Optional
import sys

class RunController:
    def __init__(self, model, view, step_mode: bool = False):
        self.model = model
        self.view = view
        self.step_mode = step_mode

        # attach view as observer
        self.model.attach(self.view)

    def run_all(self, max_cycles: Optional[int] = None):
        if self.step_mode:
            self.run_step_interactive(max_cycles=max_cycles)
        else:
            self.model.run(max_cycles=max_cycles)

    def run_step_interactive(self, max_cycles: Optional[int] = None):
        c = 0
        while self.model.running:
            _ = input("[Enter=step, q=quit] ")
            if _ and _.strip().lower().startswith('q'):
                break
            self.model.step()
            c += 1
            if max_cycles is not None and c >= max_cycles:
                break
