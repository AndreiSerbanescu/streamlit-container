import os
from common.utils import *
import subprocess as sb

class Markdown2Pdf:

    def __init__(self, report_dir):

        self.report_dir = report_dir

    def generate_pdf(self):

        markdown_filename = os.path.join(self.report_dir, "report.md")
        pdf_filename      = os.path.join(self.report_dir, "report.pdf")

        pandoc_cmd = f"pandoc -s -o {pdf_filename} {markdown_filename}"

        sb.check_output([pandoc_cmd], shell=True)

        return pdf_filename


