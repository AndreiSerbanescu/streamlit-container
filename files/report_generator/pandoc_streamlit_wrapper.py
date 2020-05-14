import streamlit as st
from common.utils import *
import os
from matplotlib import pyplot as plt

class PandocStreamlitWrapper:

    def __init__(self, base_dir="/tmp"):
        self.md_lines = []
        self.report_dir = self.__create_report_dir(base_dir)

        self.image_index = 0

    def generate_markdown_report(self):
        report_filename = os.path.join(self.report_dir, "report.md")

        with open(report_filename, "w") as md_report:
            data = "  \n\n".join(self.md_lines)
            md_report.write(data)

        return self.report_dir

    def __create_report_dir(self, base_dir):
        unique_id = get_unique_id()
        report_dir = os.path.join(base_dir, "report_generator" + unique_id)
        os.makedirs(report_dir, exist_ok=True)

        return report_dir

    def wrapper_get_lines(self):
        return self.md_lines

    def markdown(self, *args, **kwargs):
        self.md_lines.extend(args)
        st.markdown(*args, **kwargs)

    def write(self, *args, **kwargs):
        self.md_lines.extend(args)
        st.write(*args, **kwargs)

    def text(self, *args, **kwargs):
        self.md_lines.extend(args)
        st.text(*args, **kwargs)

    def pyplot(self, *args, **kwargs):



        st.pyplot(*args, **kwargs)

    def image(self, *args, **kwargs):

        if isinstance(args[0], list):

            captions = kwargs.get("caption", ["" for i in range(len(args[0]))])

            base_image_name = f"image_row_{self.image_index}"
            self.image_index += 1

            row_index = 0

            image_filenames = []

            for image in args[0]:
                image_name = base_image_name + f"_{row_index}.png"
                row_index += 1

                image_filename = os.path.join(self.report_dir, image_name)
                image.save(image_filename)

                image_filenames.append(image_filename)

            table = self.__draw_image_table(image_filenames, captions)
            self.md_lines.append(table)
        else:
            image_name = f"image_{self.image_index}.png"
            self.image_index += 1
            image_filename = os.path.join(self.report_dir, image_name)

            image = args[0]
            image.save(image_filename)

            self.md_lines.append(f"![]({image_filename}){{ width=250px }}")

        st.image(*args, **kwargs)

    def __draw_image_table(self, img_fns, captions):
        # TODO use relative filepath

        # TODO fix format per page with slice information and fat measurements per slice

        table = "--             |  --         \n" \
                ":-------------------------:|:-------------------------:|\n"

        for i in range(len(img_fns) // 2):

            image_left = img_fns[i]
            image_right = img_fns[i + 1] if i < len(img_fns) else None

            table += f'![]({image_left}){{ width=150px }}  |  ![]({image_right}){{ width=150px }} |  \n' \
                     f'{captions[i]}              | {captions[i + 1]}  | \n'

        if len(img_fns) % 2 == 1:
            table += f'![]({img_fns[-1]}){{ width=150px }}  |   |  \n' \
                     f'{captions[-1]}              |   | \n'

        return table

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            st_method = getattr(st, name)
            st_method(*args, **kwargs)

        return wrapper