from multiprocessing import Process
from common import listener_server
import requests as req
from mock import MagicMock


def test_base_listener_sends_code_200_when_worker_sends_success_true_and_no_exceptions_raised():

    def mock_request(*args, **kwargs):
        return {}, True

    def mock_mark_ready():
        pass


    served_requests = {
        "/mock_request": mock_request
    }

    process = Process(target=lambda: listener_server.start_listening(served_requests,
                    multithreaded=False, mark_as_ready_callback=mock_mark_ready))

    process.start()

    return_code = req.get("http://localhost:8000/mock_request")

    assert return_code.status_code == 200
    print("Return code", return_code)
    process.terminate()
    process.join()


def test_base_listener_sends_code_500_when_worker_sends_success_false():

    def mock_request(*args, **kwargs):
        return {}, False

    def mock_mark_ready():
        pass


    served_requests = {
        "/mock_request": mock_request
    }

    process = Process(target=lambda: listener_server.start_listening(served_requests,
                    multithreaded=False, mark_as_ready_callback=mock_mark_ready))

    process.start()

    return_code = req.get("http://localhost:8000/mock_request")

    assert return_code.status_code == 500
    print("Return code", return_code)
    process.terminate()
    process.join()


def test_base_listener_sends_code_500_when_worker_sends_exception():

    def mock_request(*args, **kwargs):

        raise Exception("Mock exception")

    def mock_mark_ready():
        pass


    served_requests = {
        "/mock_request": mock_request
    }

    process = Process(target=lambda: listener_server.start_listening(served_requests,
                    multithreaded=False, mark_as_ready_callback=mock_mark_ready))

    process.start()

    return_code = req.get("http://localhost:8000/mock_request")

    print(return_code.text)

    assert return_code.status_code == 500
    print("Return code", return_code)
    process.terminate()
    process.join()

def test_base_listener_redirects_exception_message_when_worker_sends_exception():


    exception_message = "Here is the mock exception message"

    def mock_request(*args, **kwargs):

        raise Exception(exception_message)

    def mock_mark_ready():
        pass


    served_requests = {
        "/mock_request": mock_request
    }

    process = Process(target=lambda: listener_server.start_listening(served_requests,
                    multithreaded=False, mark_as_ready_callback=mock_mark_ready))

    process.start()

    return_code = req.get("http://localhost:8000/mock_request")


    assert exception_message in return_code.text

    print("Return code", return_code)
    process.terminate()
    process.join()
