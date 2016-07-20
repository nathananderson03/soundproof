import logging
logger = logging.getLogger(__name__)

class ExceptionLogger(object):
    def process_exception(self, request, exception):
        #logger.exception(exception)
        print exception
