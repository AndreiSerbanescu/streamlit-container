import os
from common.utils import *
import subprocess as sb


class Markdown2Pdf:

    def __init__(self, report_dir, remove_files=True):

        self.report_dir = report_dir
        self.report_name = "report.pdf"
        self.remove_files = remove_files

    def generate_pdf(self):
        pandoc_cmd = f"cd {self.report_dir} && pandoc -s -o {self.report_name} report.md"

        sb.check_output([pandoc_cmd], shell=True)
        pdf_filename = os.path.join(self.report_dir, self.report_name)

        if self.remove_files:
            self.__remove_other_files()

        return pdf_filename

    def __remove_other_files(self):
        files = os.listdir(self.report_dir)
        for file in files:
            if file != self.report_name:
                os.remove(os.path.join(self.report_dir, file))