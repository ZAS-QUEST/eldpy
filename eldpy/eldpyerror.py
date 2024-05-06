class EldpyError(Exception):
    def __init__(self, message, logger=None):
        self.message = message
        if logger:
            logger.error(self.message)
