"""
utils.py
--------
Helper classes used during training.
"""


class EarlyStopping:
    """
    Stops training if validation loss doesn't improve for `patience` epochs.

    How it works:
      - After each epoch, call early_stopping(val_loss)
      - It returns True when training should stop
      - It also tells you whether the current epoch is the best (to save the model)

    Args:
        patience  : how many epochs to wait without improvement before stopping
        min_delta : minimum improvement to count as "actually better"
                    (avoids stopping for tiny random fluctuations)
    """

    def __init__(self, patience: int = 5, min_delta: float = 0.001):
        self.patience  = patience
        self.min_delta = min_delta

        self.best_loss    = float("inf")
        self.counter      = 0       # epochs without improvement
        self.should_stop  = False

    def __call__(self, val_loss: float) -> bool:
        """Returns True if training should stop."""
        if val_loss < self.best_loss - self.min_delta:
            # Improved — reset counter
            self.best_loss = val_loss
            self.counter   = 0
        else:
            # No improvement
            self.counter += 1
            print(f"  [EarlyStopping] No improvement for {self.counter}/{self.patience} epochs")
            if self.counter >= self.patience:
                self.should_stop = True

        return self.should_stop
