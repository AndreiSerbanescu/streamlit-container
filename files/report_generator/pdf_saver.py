import os

class Markdown2Pdf:

    def __init__(self, report_filename, md_lines):

        self.report_filename = report_filename
        self.md_lines = md_lines

    def generate_report(self):

        with open(self.report_filename, "w") as md_report:

            for line in self.md_lines:
                md_report.write(line + "\n")

