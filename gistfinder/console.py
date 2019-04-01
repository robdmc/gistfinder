#!/usr/bin/env python
from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import VSplit, Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.filters import to_filter
from prompt_toolkit.styles import Style
from pygments.lexers import Python3Lexer

from prompt_toolkit.layout import Margin, NumberedMargin, ScrollbarMargin
from prompt_toolkit.lexers import PygmentsLexer

from .loader import Loader


LIPSUM = '\n'.join(''.join([f'{x} '] * 10) for x in range(1000))
lips_lines = LIPSUM.split('\n')


def list_row_change(buffer):
    app_state = buffer.app_state
    doc = buffer.document
    pos = doc.cursor_position_row

    content_buffer = app_state.content_buffer
    content_buffer.read_only = to_filter(False)
    content_buffer.text = app_state.code(pos)
    content_buffer.read_only = to_filter(True)


class AppState:
    def __init__(self, loader):
        self.loader = loader

        self.search_buffer = Buffer(on_cursor_position_changed=list_row_change)  # Editable buffer.
        self.search_buffer.text = '\n'.join(self.list_lines)

        self.search_buffer.read_only = to_filter(True)
        self.search_buffer.app_state = self

        self.content_buffer = Buffer()  # Editable buffer.
        self.content_buffer.text = self.list_lines[0]
        self.content_buffer.read_only = to_filter(True)
        self.content_buffer.app_state = self

    @property
    def list_lines(self):
        return [r['file_name'] for r in self.loader.records.values()]

    def code(self, ind):
        return list(self.loader.records.values())[ind]['code']


class MyMargin(Margin):
    def get_width(self):
        return 1


state = AppState(Loader())


root_container = VSplit([
    Window(
        width=55,
        left_margins=[NumberedMargin()],
        right_margins=[ScrollbarMargin()],
        content=BufferControl(buffer=state.search_buffer, focusable=True),
        cursorline=True
    ),
    # Window(width=1, char='|'),
    Window(
        left_margins=[NumberedMargin()],
        content=BufferControl(buffer=state.content_buffer, focusable=True, lexer=PygmentsLexer(Python3Lexer)),
        ignore_content_width=True
    ),
])


kb = KeyBindings()


@kb.add('c-c')
def _(event):
    " Quit application. "
    event.app.exit()


def cli():

    layout = Layout(root_container)

    style = Style(
        [
            # ('cursor-line', 'fg:ansiblack bg:ansicyan'),
            ('cursor-line', 'fg:ansiwhite bg:#003366'),
            ('cursor-line', 'fg:#CCCCCC bg:#003366'),
        ]
    )

    app = Application(
        layout=layout,
        full_screen=True,
        key_bindings=kb,
        editing_mode=EditingMode.VI,
        mouse_support=True,
        style=style,
    )
    state.app = app

    app.run()
