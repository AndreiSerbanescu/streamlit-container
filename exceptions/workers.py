
class WorkerFailedException(Exception):
    def __init__(self, worker_hostname):
        super(WorkerFailedException, self).__init__(self)
        self.worker_name = worker_hostname

class WorkerNotReadyException(Exception):
    def __init__(self, worker_hostname):
        super(WorkerNotReadyException, self).__init__(self)
        self.worker_name = worker_hostname