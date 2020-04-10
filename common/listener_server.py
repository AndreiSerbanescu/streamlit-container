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

    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "text")
        self.end_headers()


    def do_GET(self):
        self._set_headers()
        self.__handle_request()

    def __handle_request(self):
        parsed_url = urlparse(self.path)
        parsed_params = parse_qs(parsed_url.query)

        log_debug("Got request with url {} and params {}".format(parsed_url.path, parsed_params))

        if parsed_url.path not in self.__requested_method:
            log_debug("unkown request {} received".format(self.path))
            return


        log_debug("running {}".format(os.environ["HOSTNAME"]))
        result_dict = self.__requested_method[parsed_url.path](parsed_params)
        log_debug("result", result_dict)

        log_debug("sending over", result_dict)
        self.wfile.write(json.dumps(result_dict).encode())


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