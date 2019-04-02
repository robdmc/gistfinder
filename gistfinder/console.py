#!/usr/bin/env python
import sys
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
        self.content_buffer.text = self.code(0)
        self.content_buffer.read_only = to_filter(True)
        self.content_buffer.app_state = self
        self._index = 0

    @property
    def list_lines(self):
        return [r['file_name'] for r in self.loader.records.values()]

    @property
    def descriptions(self):
        return [r['description'] for r in self.loader.records.values()]

    def code(self, index):
        self._index = index
        return list(self.loader.records.values())[self._index]['code']

    @property
    def selected_code(self):
        return self.code(self._index)

    @property
    def selected_file_name(self):
        return self.list_lines[self._index]

    @property
    def selected_description(self):
        return self.descriptions[self._index]

    def print(self):
        print('\n', file=sys.stderr)
        print(('>' * 20) + ' ' + self.selected_file_name + ' ' + ('<' * 20), file=sys.stderr)
        print(file=sys.stderr)
        print(self.selected_code, file=sys.stderr)
        print('', file=sys.stderr)
        print(('>' * 30) + ('<' * 30), file=sys.stderr)
        print('\n', file=sys.stderr)



state = AppState(Loader())


root_container = VSplit([
    Window(
        width=55,
        left_margins=[NumberedMargin()],
        content=BufferControl(buffer=state.search_buffer, focusable=True),
        cursorline=True,
        # style='bg:#B0A0CB fg:black',
        style='bg:#AE9EC9 fg:black',
        # style='bg:#154360 fg:white',
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

@kb.add('enter')
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
    app.state = state

    app.run()

    state.print()
