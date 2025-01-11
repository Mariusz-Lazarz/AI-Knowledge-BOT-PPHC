import threading
import itertools
import time

class Spinner:
    def __init__(self, message="Processing..."):
        """
        Initializes the spinner with a custom message.

        Parameters:
            message (str): The message to display with the spinner.
        """
        self.message = message
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._spin)

    def _spin(self):
        """
        Internal method to display the spinner animation.
        """
        for char in itertools.cycle('|/-\\'):
            if self.stop_event.is_set():
                break
            print(f'\r{self.message} {char}', end='', flush=True)
            time.sleep(0.1)
        print('\r', end='', flush=True)  # Clear the spinner line

    def start(self):
        """
        Starts the spinner in a separate thread.
        """
        self.thread.start()

    def stop(self):
        """
        Stops the spinner and waits for the thread to finish.
        """
        self.stop_event.set()
        self.thread.join()
