from http.server import *
from urllib.parse import urlparse
from urllib.parse import parse_qs
from common.utils import *
from socketserver import ThreadingMixIn
import json
from functools import partial


class CommandRequestHandler(BaseHTTPRequestHandler):

    def __init__(self, served_requests, *args, **kwargs):
        self.__requested_method = served_requests
        super().__init__(*args, **kwargs)

    def _set_headers(self, response_code):
        self.send_response(response_code)
        self.send_header("Content-type", "text")
        self.end_headers()


    def do_GET(self):
        self.__handle_request()

    def send_answer(self, success, message):
        response_code = 200 if success else 500

        self._set_headers(response_code)
        self.wfile.write(message.encode())

    def __handle_request(self):
        parsed_url = urlparse(self.path)
        parsed_params = parse_qs(parsed_url.query)

        log_debug("Got request with url {} and params {}".format(parsed_url.path, parsed_params))

        if parsed_url.path not in self.__requested_method:
            log_debug("unkown request {} received".format(self.path))
            self.send_answer(success=False, message="Unkown request {} received".format(self.path))
            return


        log_debug("running {}".format(os.environ["HOSTNAME"]))

        try:
            result_dict, success = self.__requested_method[parsed_url.path](parsed_params)

            if not success:
                log_debug("Worker not successful")
                self.send_answer(success=False, message="Worker could not finish computation")
                return

            log_debug("result", result_dict)

            log_debug("sending over", result_dict)

            self.send_answer(success=True, message=json.dumps(result_dict))
            return

        except Exception as e:
            log_debug("Caught exceptiton", e)
            self.send_answer(success=False, message="Error encountered {}".format(str(e)))
            return




class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    pass




def start_listening(requests_served, multithreaded=False, mark_as_ready_callback=None):

    server_address = ('', 8000)

    server_class = ThreadingSimpleServer if multithreaded else HTTPServer

    # partial partially initialises the command request handler
    # by only sending requests_served to its constructor
    handler = partial(CommandRequestHandler, requests_served)
    httpd = server_class(server_address, handler)

    if mark_as_ready_callback is not None:
        mark_as_ready_callback()

    httpd.serve_forever()