#!/usr/bin/env python

import warnings
warnings.filterwarnings("ignore")

import re
import sys

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import VSplit, Window, HSplit
from prompt_toolkit.layout.controls import BufferControl


from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.filters import to_filter, Condition
from prompt_toolkit.styles import Style
from pygments.lexers import Python3Lexer

from prompt_toolkit.layout import NumberedMargin
from prompt_toolkit.lexers import PygmentsLexer
import click

from gistfinder.sync import Updater
from .loader import Loader
#  from .utils import print_temp

from prompt_toolkit.application.current import get_app


@Condition
def not_in_search_mode():
    app = get_app()
    return app.state.layout.current_window != app.state.search_window


class AppState:
    SEARCH_DEFAULT_TEXT = r' Search:/  Window:<space> Select:<enter> Exit:<ctrl-c> '

    def __init__(self, loader):
        self.glob_expr = None
        self.text_expr = None
        self.desc_expr = None
        self.file_expr = None
        self.code_expr = None

        self.loader = loader

        self.list_buffer = Buffer(on_cursor_position_changed=self.list_row_change)  # Editable buffer.
        # self.list_buffer.text = '\n'.join(self.list_lines)
        self.sync_list_lines()

        self.list_buffer.read_only = to_filter(True)
        self.list_buffer.app_state = self

        self.content_buffer = Buffer()  # Editable buffer.
        self.content_buffer.text = self.code(0)
        self.content_buffer.read_only = to_filter(True)
        self.content_buffer.app_state = self

        self.search_buffer = Buffer(on_text_changed=self.search_text_change)
        self.search_buffer.app_state = self
        self.search_buffer.read_only = to_filter(True)

        self.description_buffer = Buffer()
        self.description_buffer.app_state = self
        self.description_buffer.read_only = to_filter(True)

        self.slash_buffer = Buffer()
        self.slash_buffer.app_state = self
        self.slash_buffer.read_only = to_filter(True)

        self._index = 0
        self.print_on_exit = False

        self._list_lines = None

    def sync_list_lines(self):
        self.list_buffer.read_only = to_filter(False)
        self.list_buffer.text = '\n'.join(self.list_lines)
        self.list_buffer.read_only = to_filter(True)

    def clear_searches(self):
        self.glob_expr = None
        self.text_expr = None
        self.desc_expr = None
        self.file_expr = None
        self.code_expr = None

    @property
    def list_recs(self):
        return self.loader.get(
            glob_expr=self.glob_expr,
            text_expr=self.text_expr,
            desc_expr=self.desc_expr,
            file_expr=self.file_expr,
            code_expr=self.code_expr
        )

    @property
    def list_lines(self):
        return [r['file_name'] for r in self.list_recs.values()]

    @property
    def descriptions(self):
        return [r['description'] for r in self.loader.records.values()]

    def search_text_change(self, buffer):
        # rex_glob = re.compile(r'\\g([^\\]+)')
        # rex_code = re.compile(r'\\c([^\\]+)')
        # rex_file = re.compile(r'\\f([^\\]+)')
        # rex_text = re.compile(r'\\t([^\\]+)')
        rex_text = re.compile(r'([^\\]+)')
        rex_slash = re.compile(r'\\\s*$')
        rex_space = re.compile(r'^\s*$')

        app_state = buffer.app_state

        query = buffer.text
        # m_glob = rex_glob.search(query)
        # m_code = rex_code.search(query)
        # m_file = rex_file.search(query)
        m_text = rex_text.search(query)
        m_slash = rex_slash.search(query)
        m_space = rex_space.search(query)

        self.clear_searches()

        if m_slash or m_space:
            return

        # if m_glob:
        #     self.glob_expr = m_glob.group(1)
        # if m_code:
        #     self.code_expr = m_code.group(1)
        # if m_file:
        #     self.file_expr = m_file.group(1)
        # if m_text:
        #     self.text_expr = m_text.group(1)

        # if not any([bool(m) for m in [m_glob, m_code, m_file, m_text]]):
        # self.text_expr = query
        self.text_expr = m_text.group(1)

        app_state.sync_list_lines()
        self.set_code(0)
        self.set_description(0)
        return

    def list_row_change(self, buffer):
        doc = buffer.document
        pos = doc.cursor_position_row

        self.set_code(pos)
        self.set_description(pos)

    def code(self, index):
        self._index = index
        if self.list_recs:
            return list(self.list_recs.values())[self._index]['code']
        else:
            return ''

    def description(self, index):
        self._index = index
        if self.list_recs:
            return list(self.list_recs.values())[self._index]['description']
        else:
            return ''

    def set_code(self, index):
        content_buffer = self.content_buffer
        content_buffer.read_only = to_filter(False)
        content_buffer.text = self.code(index)
        content_buffer.read_only = to_filter(True)

    def set_description(self, index):
        description_buffer = self.description_buffer
        description_buffer.read_only = to_filter(False)
        description_buffer.text = f'   {self.description(index)}'
        description_buffer.read_only = to_filter(True)

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
        print(file=sys.stderr)
        print(self.selected_code, file=sys.stderr)
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
            style='bg:#AE9EC9 fg:black',
        )

        code_window = Window(
            left_margins=[NumberedMargin()],
            content=BufferControl(buffer=self.state.content_buffer, focusable=True, lexer=PygmentsLexer(Python3Lexer)),
            ignore_content_width=True
        )
        description_window = Window(
            content=BufferControl(
                buffer=self.state.description_buffer,
                focusable=False,
                # key_bindings=self.get_search_key_bindings(),
            ),
            height=1,
            style='bg:#1B2631  fg:#F1C40F',
        )

        search_window = Window(
            content=BufferControl(
                buffer=self.state.search_buffer,
                focusable=True,
                key_bindings=self.get_search_key_bindings(),
            ),
            height=1,
            style='bg:#1B2631  fg:#F1C40F',
        )

        slash_window = Window(
            content=BufferControl(
                buffer=self.state.slash_buffer,
                focusable=False,
            ),
            height=1,
            width=1,
            style='bg:#1B2631  fg:#F1C40F',
        )

        self.state.register_windows(list_window, code_window)
        self.state.search_window = search_window

        main_container = VSplit([list_window, code_window])
        search_container = VSplit([slash_window, search_window])

        root_container = HSplit([
            description_window,
            main_container,
            search_container,
        ])
        return root_container

    def get_search_key_bindings(self):
        kb = KeyBindings()

        @kb.add('enter', eager=True)
        def _(event):
            window_to_focus = event.app.state.focus_window(0)
            event.app.layout.focus(window_to_focus)
            event.app.state.sync_list_lines()

        return kb

    def get_key_bindings(self):
        kb = KeyBindings()

        @kb.add('c-c')
        def _(event):
            " Quit application. "
            event.app.exit()

        @kb.add('c-q')
        def _(event):
            " Quit application. "
            event.app.exit()

        @kb.add('enter')
        def _(event):
            " Quit application. "
            event.app.state.print_on_exit = True
            event.app.exit()

        @kb.add('space', filter=not_in_search_mode)
        def _(event):
            " Quit application. "
            window_to_focus = event.app.state.next_window()
            event.app.layout.focus(window_to_focus)

        @kb.add('/')
        def _(event):
            " Go into search mode "
            window_to_focus = event.app.state.search_window
            event.app.layout.focus(window_to_focus)
            event.app.state.search_buffer.read_only = to_filter(False)
            event.app.state.search_buffer.text = ''

            event.app.state.slash_buffer.read_only = to_filter(False)
            event.app.state.slash_buffer.text = '/'
            event.app.state.slash_buffer.read_only = to_filter(True)

        @kb.add('escape')
        def _(event):
            " Get out of search mode "
            window_to_focus = event.app.state.focus_window(0)
            event.app.layout.focus(window_to_focus)
            event.app.state.search_buffer.text = AppState.SEARCH_DEFAULT_TEXT
            event.app.state.search_buffer.read_only = to_filter(True)

            event.app.state.slash_buffer.read_only = to_filter(False)
            event.app.state.slash_buffer.text = ''
            event.app.state.slash_buffer.read_only = to_filter(True)

            event.app.state.clear_searches()
            event.app.state.sync_list_lines()

        return kb

    def run(self):
        root_container = self.get_container()
        kb = self.get_key_bindings()

        layout = Layout(root_container)
        style = Style(
            [
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
        self.state.layout = layout
        app.state = self.state

        import logging
        logger = logging.getLogger()
        logger.setLevel(logging.CRITICAL)

        app.run()
        self.state.print()


@click.command(help='A CLI tool for searching your gists')
@click.option('-u', '--user', help='Set up github user')
@click.option('-t', '--token', help='Set up github token')
@click.option('-s', '--sync', is_flag=True, help='Sync updated gists')
@click.option('-r', '--reset', is_flag=True, help='Delete and resync all gists')
@click.option('--fake', is_flag=True, help='Delete and resync all gists')
def cli(user, token, sync, reset, fake):
    updater = Updater()
    if reset:
        updater.reset()
    elif sync:
        updater.sync()
    elif token or user:
        if token:
            updater.set_github_token(token)
        if user:
            updater.set_github_user(user)

        print()
        print('Wrote config to: {}'.format(updater.auth_file))
        print()

    else:
        UI().run()
