import streamlit as st
from common.utils import *
import time
import os

class PandocStreamlitWrapper:

    def __init__(self):
        self.md_lines = []

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

    def image(self, *args, **kwargs):
        self.md_lines.extend(["###  IMAGES HERE", str(*args), str(**kwargs)])

        st.image(*args, **kwargs)

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            st_method = getattr(st, name)
            st_method(*args, **kwargs)

        return wrapper