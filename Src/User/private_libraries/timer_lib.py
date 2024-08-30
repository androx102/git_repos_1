import time

class timer():
    """
    # This is self-made simple software timer
    """

    def __init__(self):
        """
        # Constructor
        """
        print("TIMER CONSTRUCTOR")
        self.start_time = None

    def start(self):
        """
        # TODO description
        """
        self.start_time = time.time()

    def read(self):
        """
        # TODO description
        """
        if self.start_time is not None:
            return time.time() - self.start_time
        else:
            pass
    
    def reset_timer(self):
        """
        # TODO description
        """
        self.set_timer()