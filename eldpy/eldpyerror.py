class EldpyError(Exception):
    def __init__(self, message, logger):
        self.message = message
        logger.error(self.message)
