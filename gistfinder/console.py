#!/usr/bin/env python
import sys
from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import VSplit, Window, HSplit
from prompt_toolkit.layout.controls import BufferControl


from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.filters import to_filter
from prompt_toolkit.styles import Style
from pygments.lexers import Python3Lexer

from prompt_toolkit.layout import Margin, NumberedMargin, ScrollbarMargin
from prompt_toolkit.lexers import PygmentsLexer
import click

from gistfinder.sync import Updater
from .loader import Loader
from .config import Config


class AppState:
    def __init__(self, loader):
        self.loader = loader

        self.list_buffer = Buffer(on_cursor_position_changed=self.list_row_change)  # Editable buffer.
        self.list_buffer.text = '\n'.join(self.list_lines)

        self.list_buffer.read_only = to_filter(True)
        self.list_buffer.app_state = self

        self.content_buffer = Buffer()  # Editable buffer.
        self.content_buffer.text = self.code(0)
        self.content_buffer.read_only = to_filter(True)
        self.content_buffer.app_state = self

        help_text = ' Search:/  Window:<space> Select:<enter> Exit:<ctrl-c>  Help:<ctrl-h>'
        self.search_buffer = Buffer()  # Editable buffer.
        self.search_buffer.text = help_text
        self.search_buffer.read_only = to_filter(True)
        self.search_buffer.app_state = self


        self._index = 0
        self.print_on_exit = False

    @property
    def list_lines(self):
        return [r['file_name'] for r in self.loader.records.values()]

    @property
    def descriptions(self):
        return [r['description'] for r in self.loader.records.values()]

    def list_row_change(self, buffer):
        app_state = buffer.app_state
        doc = buffer.document
        pos = doc.cursor_position_row

        content_buffer = app_state.content_buffer
        content_buffer.read_only = to_filter(False)
        content_buffer.text = app_state.code(pos)
        content_buffer.read_only = to_filter(True)

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
        if not self.print_on_exit:
            return
        print('\n', file=sys.stderr)
        print(('>' * 20) + ' ' + self.selected_file_name + ' ' + ('<' * 20), file=sys.stderr)
        print(file=sys.stderr)
        print(self.selected_code, file=sys.stderr)
        print('', file=sys.stderr)
        print(('>' * 30) + ('<' * 30), file=sys.stderr)
        print('', file=sys.stderr)

    def register_windows(self, *windows):
        self.windows = windows
        self.current_window_index = 0

    def focus_window(self, index):
        self.current_window_index = index
        return self.current_window

    def next_window(self):
        self.current_window_index = (self.current_window_index + 1) % len(self.windows)
        return self.current_window

    @property
    def current_window(self):
        return self.windows[self.current_window_index]


class UI:
    def __init__(self):
        loader = Loader()
        if not loader.has_tables:
            msg = 'You must run sync command'
            print(msg, file=sys.stderr)
            sys.exit(1)

        self.state = AppState(loader)

    def get_container(self):

        list_window = Window(
            width=55,
            left_margins=[NumberedMargin()],
            content=BufferControl(buffer=self.state.list_buffer, focusable=True),
            cursorline=True,
            # style='bg:#B0A0CB fg:black',
            style='bg:#AE9EC9 fg:black',
            # style='bg:#154360 fg:white',
        )

        code_window = Window(
                left_margins=[NumberedMargin()],
                content=BufferControl(buffer=self.state.content_buffer, focusable=True, lexer=PygmentsLexer(Python3Lexer)),
                ignore_content_width=True
        )

        search_window = Window(
            content=BufferControl(buffer=self.state.search_buffer, focusable=True),
            height=1,
            style='bg:#1B2631  fg:#F1C40F',
        )

        self.state.register_windows(list_window, code_window)
        self.state.search_window = search_window

        main_container = VSplit([list_window, code_window])


        root_container = HSplit([
            main_container,
            search_window
        ])
        return root_container



    def get_key_bindings(self):
        kb = KeyBindings()


        @kb.add('c-c')
        def _(event):
            " Quit application. "
            event.app.exit()

        @kb.add('enter')
        def _(event):
            " Quit application. "
            event.app.state.print_on_exit = True
            event.app.exit()

        @kb.add('space')
        def _(event):
            " Quit application. "
            window_to_focus = event.app.state.next_window()
            event.app.layout.focus(window_to_focus)

        @kb.add('/')
        def _(event):
            " Quit application. "
            window_to_focus = event.app.state.search_window
            event.app.layout.focus(window_to_focus)

        @kb.add('escape')
        def _(event):
            " Quit application. "
            window_to_focus = event.app.state.focus_window(0)
            event.app.layout.focus(window_to_focus)

        return kb

    def run(self):
        # loader = Loader()
        # if not loader.has_tables:
        #     msg = 'You must run sync command'
        #     print(msg, file=sys.stderr)
        #     sys.exit(1)
        #
        # state = AppState(loader)
        # ui = UI(state)
        #
        # root_container = ui.get_container(state)
        # kb = ui.get_key_bindings()
        root_container = self.get_container()
        kb = self.get_key_bindings()

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
        self.state.app = app
        app.state = self.state

        app.run()
        self.state.print()

@click.command(help='A CLI tool for searching your gists')
@click.option('-t', '--token', help='Set up github token')
@click.option('-s', '--sync', is_flag=True, help='Sync updated gists')
@click.option('-r', '--reset', is_flag=True, help='Delete and resync all gists')
@click.option('--fake', is_flag=True, help='Delete and resync all gists')
def cli(token, sync, reset, fake):
    if fake:
        Updater().rob()
        return
    if reset:
        Updater().reset()
    elif sync:
        Updater().sync()
    elif token:
        Config().set_github_token(token)
    else:
        UI().run()
