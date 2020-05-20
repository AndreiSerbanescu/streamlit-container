import streamlit as st
from common.utils import *
import os
from matplotlib import pyplot as plt
import io

class PandocStreamlitWrapper:

    def __init__(self, base_dir="/tmp"):
        self.md_lines = []
        self.report_dir = self.__create_report_dir(base_dir)

        self.image_index = 0
        self.plot_index = 0

    def generate_markdown_report(self):
        report_filename = os.path.join(self.report_dir, "report.md")

        self.md_lines = self.__draw_introduction()

        with open(report_filename, "w") as md_report:
            data = "  \n\n".join(self.md_lines)
            md_report.write(data)

        return self.report_dir

    def __draw_introduction(self):
        intro_lines = []

        intro_lines.append('# CoViD-19 Risk Calculator')
        # TODO additional introduction information

        return intro_lines + self.md_lines

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


    def pyplot(self, fig=None, clear_figure=True, **kwargs):

        # code partially taken from streamlit pyplot implementation

        if fig is None:
            fig = plt

        # Normally, dpi is set to 'figure', and the figure's dpi is set to 100.
        # So here we pick double of that to make things look good in a high
        # DPI display.
        options = {"dpi": 200, "format": "png"}

        # If some of the options are passed in from kwargs then replace
        # the values in options with the ones from kwargs
        options = {a: kwargs.get(a, b) for a, b in options.items()}
        # Merge options back into kwargs.
        kwargs.update(options)

        image_name = f"plot_{self.plot_index}.png"
        self.plot_index += 1
        image_filename = os.path.join(self.report_dir, image_name)

        fig.savefig(image_filename, **kwargs)

        self.md_lines.append(f"![]({image_filename})")

        st.pyplot(fig=fig, clear_figure=clear_figure, **kwargs)

    def image(self, *args, **kwargs):

        if isinstance(args[0], list):
            captions = kwargs.get("caption", ["" for i in range(len(args[0]))])
            table = self.__generate_table(args[0], captions)
            self.md_lines.append(table)
        else:
            table = self.__generate_mono_table(args[0])
            self.md_lines.append(table)

        st.image(*args, **kwargs)

    def __generate_mono_table(self, image):
        image_name = f"image_{self.image_index}.png"
        self.image_index += 1
        image_filename = os.path.join(self.report_dir, image_name)

        image.save(image_filename)

        return self.__draw_mono_table(image_name)

    def __draw_mono_table(self, image_filename):
        # f"![]({image_filename}){{ width=250px }}"

        return f"![]({image_filename}){{ width=250px }}  |\n"


    def __generate_table(self, images, captions):

        base_image_name = f"image_row_{self.image_index}"
        self.image_index += 1

        row_index = 0

        image_filenames = []

        for image in images:
            image_name = base_image_name + f"_{row_index}.png"
            row_index += 1

            image_filename = os.path.join(self.report_dir, image_name)
            image.save(image_filename)

            image_filenames.append(image_name)

        return self.__draw_image_table(image_filenames, captions)

    def __draw_image_table(self, img_fns, captions):

        table = "--             |  --         \n" \
                ":-------------------------:|:-------------------------:|\n"

        for i in range(0, len(img_fns) - 1, 2):

            image_left = img_fns[i]
            image_right = img_fns[i + 1]

            caption_left = captions[i]
            captions_right = captions[i + 1]

            table += f'![]({image_left}){{ width=150px }}  |  ![]({image_right}){{ width=150px }} |  \n' \
                     f'{caption_left}              | {captions_right}  | \n'

        if len(img_fns) % 2 == 1:
            table += f'![]({img_fns[-1]}){{ width=150px }}  |   |  \n' \
                     f'{captions[-1]}              |   | \n'

        table += '\n'

        return table

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            st_method = getattr(st, name)
            st_method(*args, **kwargs)

        return wrapper