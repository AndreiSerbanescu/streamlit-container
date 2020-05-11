import http.server
import socketserver
import os


class FileServer:

    def __init__(self, port, base_dir, handler=None):
        self.port = port
        self.handler = handler if handler is not None else http.server.SimpleHTTPRequestHandler
        self.base_dir = base_dir
    def start(self):
        os.chdir(self.base_dir)
        with socketserver.ThreadingTCPServer(("", self.port), self.handler) as httpd:
            print(f"Started fileserver at localhost {self.port}")
            httpd.serve_forever()

def start_file_server():

    fs_port = int(os.environ["FILESERVER_PORT"])
    fs_base_dir = os.environ["FILESERVER_BASE_DIR"]
    os.makedirs(fs_base_dir, exist_ok=True)

    fs = FileServer(fs_port, fs_base_dir)
    fs.start()
    
if __name__ == "__main__":
    start_file_server()