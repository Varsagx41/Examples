# coding=UTF-8
import curses, curses.panel
import random
import pprint
import time
import inspect
from collections import OrderedDict
from _shapes_manager import *
from _shapes import UsersShape, WavesShape
import locale


locale.setlocale(locale.LC_ALL, '')


unimap = {
    'small': {
        '0': u'\u2080',
        '1': u'\u2081',
        '2': u'\u2082',
        '3': u'\u2083',
        '4': u'\u2084',
        '5': u'\u2085',
        '6': u'\u2086',
        '7': u'\u2087',
        '8': u'\u2088',
        '9': u'\u2089',
        'x': u'\u2093',
    },
    'border': {
        'double': {
            'hline': u'\u2550',
            'vline': u'\u2551',
            'ulc': u'\u2554',
            'urc': u'\u2557',
            'dlc': u'\u255a',
            'drc': u'\u255d',
        },
    },
}

def log(s):
    s = pprint.pformat(s)
    open('/tmp/test.gui', 'a+').write(str(s) + '\n')
log('-'*78)

class IO(object):

    def __init__(self, gui):
        self.call_table = {}
        self.gui = gui
        self.screen = gui.screen
        self.init_keys()
        self.mode = 'default'
        self.text = ''
        self.editor_cursor = 0

    def init_keys(self):
        self.keys = {
            'DOWN': curses.KEY_DOWN,
            'LEFT': curses.KEY_LEFT,
            'RIGHT': curses.KEY_RIGHT,
            'UP': curses.KEY_UP,
            'BACKSPACE': curses.KEY_BACKSPACE,
            'ESC': 0x1b,
            'ENTER': 0x0a,
            'SPACE': 0x20,
            'RESIZE': curses.KEY_RESIZE,
            '_MOUSE_EVENT': '_MOUSE_EVENT',
            '_ANY': '_ANY',
        }

    def register(self, key, function, mode='default'):
        if mode not in self.call_table:
            self.call_table[mode] = {}
        if type(key) != int:
            key = self.keys[key.upper()]

        self.call_table[mode][key] = function

    def unregister(self, key, mode='default'):
        if mode in self.call_table:
            if type(key) != int:
                key = self.keys[key]

            self.call_table[mode].pop(key, None)

    def clean(self, mode=None):
        if mode:
            self.call_table[mode] = {}
        else:
            self.call_table = {}

    def change_mode(self, mode):
        while True:
            key = self.screen.getch()
            if key == -1:
                break
        if mode not in self.call_table:
            self.call_table[mode] = {}
        if mode == 'editor':
            self.init_editor()
        elif self.mode == 'editor':
            self.del_editor()
        self.mode = mode

    def init_editor(self):
        curses.curs_set(1)
        self.text = ''
        self.editor_cursor = 0

    def del_editor(self):
        curses.curs_set(0)
        self.text = ''
        self.editor_cursor = 0

    def configure_editor(self, text='', color=None, cursor=None):
        self.text = text
        self.color = color
        if cursor:
            self.editor_cursor = cursor
        else:
            self.editor_cursor = len(self.text)

    def editor(self):
        color = self.color or 0
        while True:
            key = self.screen.getch()
            if key < 0:
                break
            cy, cx = curses.getsyx()
            if key == 27:  # ESC or ALT
                k = self.screen.getch()
                if k == -1:
                    if key in self.call_table[self.mode]:
                        self.call_table[self.mode][key](self.text)
            elif key in self.call_table[self.mode]:
                self.call_table[self.mode][key](self.text)
            elif key >= 0x20 and key <= 0x7e:
                self.text = self.text[:self.editor_cursor] + chr(key) + self.text[self.editor_cursor:]
                try:
                    self.screen.echochar(key, color)
                    self.editor_cursor += 1
                except:
                    pass
            elif key == curses.KEY_BACKSPACE:
                if self.editor_cursor > 0 and self.editor_cursor <= len(self.text):
                    self.screen.move(cy, cx - 1)
                    self.editor_cursor -= 1
                    self.screen.delch()
                    self.text = self.text[:self.editor_cursor] + self.text[self.editor_cursor + 1:]
                    self.screen.insch(cy, cx + len(self.text) - self.editor_cursor - 1, ' ', self.color)
                    self.screen.move(cy, cx - 1)
            elif key == curses.KEY_DC:
                if self.editor_cursor >= 0 and self.editor_cursor < len(self.text):
                    self.screen.delch()
                    self.text = self.text[:self.editor_cursor] + self.text[self.editor_cursor + 1:]
                    self.screen.insch(cy, cx + len(self.text) - self.editor_cursor, ' ', self.color)
                    self.screen.move(cy, cx)
            elif key == curses.KEY_LEFT:
                if self.editor_cursor > 0:
                    self.editor_cursor -= 1
                    self.screen.move(cy, cx - 1)
            elif key == curses.KEY_RIGHT:
                if self.editor_cursor < len(self.text):
                    self.editor_cursor += 1
                    self.screen.move(cy, cx + 1)

            elif key == curses.KEY_RESIZE:
                if key in self.call_table[self.mode]:
                    self.call_table[self.mode][key](self.text)
                elif key in self.call_table['default']:
                    self.call_table['default'][key]()

    def react(self):
        if self.mode == 'editor':
            self.editor()
            return
        while True:
            key = self.screen.getch()
            if key < 0:
                break
            if key == curses.KEY_RESIZE:
                if key in self.call_table[self.mode]:
                    self.call_table[self.mode][key]()
                elif key in self.call_table['default']:
                    self.call_table['default'][key]()
            elif '_ANY' in self.call_table[self.mode]:
                self.call_table[self.mode]['_ANY'](key)
            elif key == curses.KEY_MOUSE:
                try:
                    id, x, y, z, button = curses.getmouse()
                    if '_MOUSE_EVENT' in self.call_table[self.mode]:
                        self.call_table[self.mode]['_MOUSE_EVENT'](x=x, y=y, button=button)
                except Exception, e:
                    log('ERROR: ' + str(e))
            else:
                if key == 27:  # ESC or ALT
                    k = self.screen.getch()
                    if k == -1:
                        if key in self.call_table[self.mode]:
                            self.call_table[self.mode][key]()
                elif key in self.call_table[self.mode]:
                    self.call_table[self.mode][key]()


themes = {
    'default': {
        'default': (curses.COLOR_WHITE, curses.COLOR_BLACK, None),
        'bg': (curses.COLOR_BLACK, curses.COLOR_WHITE, None),
        'border': (curses.COLOR_WHITE, curses.COLOR_CYAN, None),
        'input': (curses.COLOR_WHITE, curses.COLOR_BLUE, None),
        'vertex_disabled': {
            'border': (curses.COLOR_BLACK, curses.COLOR_WHITE, None),
            'text': (curses.COLOR_BLACK, curses.COLOR_WHITE, None),
            'space': (curses.COLOR_BLACK, curses.COLOR_WHITE, None),
            'edges': (curses.COLOR_BLACK, curses.COLOR_WHITE, None),
        },
        'vertex_enabled': {
            'border': (curses.COLOR_GREEN, curses.COLOR_WHITE, None),
            'text': (curses.COLOR_GREEN, curses.COLOR_WHITE, None),
            'space': (curses.COLOR_GREEN, curses.COLOR_WHITE, None),
            'edges': (curses.COLOR_GREEN, curses.COLOR_WHITE, None),
        },
        'vertex_selected_disabled': {
            'border': (curses.COLOR_BLACK, curses.COLOR_YELLOW, None),
            'text': (curses.COLOR_BLACK, curses.COLOR_YELLOW, None),
            'space': (curses.COLOR_BLACK, curses.COLOR_YELLOW, None),
            'edges': (curses.COLOR_BLACK, curses.COLOR_YELLOW, None),
        },
        'vertex_selected_enabled': {
            'border': (curses.COLOR_GREEN, curses.COLOR_YELLOW, None),
            'text': (curses.COLOR_GREEN, curses.COLOR_YELLOW, None),
            'space': (curses.COLOR_GREEN, curses.COLOR_YELLOW, None),
            'edges': (curses.COLOR_GREEN, curses.COLOR_YELLOW, None),
        },
        'notification': {
            'border': (curses.COLOR_WHITE, curses.COLOR_BLACK, None),
            'text': {
                'default': (curses.COLOR_WHITE, curses.COLOR_BLACK, None),
                'success': (curses.COLOR_GREEN, curses.COLOR_BLACK, None),
                'warning': (curses.COLOR_YELLOW, curses.COLOR_BLACK, None),
                'error': (curses.COLOR_RED, curses.COLOR_BLACK, None),
            },
        }
    },
}


class Theme(object):

    def __init__(self, themes):
        self.counter = 1
        self.current_theme = None
        self.themes = themes
        self.map = {}

    def __len__(self):
        return len(self.map)

    def __getitem__(self, key):
        return self.map[key]

    def __iter__(self):
        return self.map.iteritems()

    def __contains__(self, key):
        return key in self.map

    def _init_map(self, theme, obj):
        for name, color in theme.iteritems():
            colortype = type(color)
            if colortype == dict:
                obj[name] = {}
                self._init_map(color, obj[name])
            else:
                curses.init_pair(self.counter, color[0], color[1])
                obj[name] = {'color': curses.color_pair(self.counter),
                             'tile': color[2] or ' '}
                self.counter += 1

    def pick(self, themename):
        if themename in self.themes:
            self._init_map(self.themes[themename], self.map)
            self.current_theme = themename


class State(object):

    def __init__(self):
        self._state = {}
        self._state['_changed'] = True
        self._controlled = []

    def __len__(self):
        return len(self._state)

    def __getitem__(self, key):
        keytype = type(key)
        if keytype == list or keytype == tuple:
            return [self._state[k] for k in key]
        else:
            return self._state[key]

    def __setitem__(self, key, value):
        keytype = type(key)
        if keytype == list or keytype == tuple:
            for i in range(len(key)):
                self._state[key[i]] = value[i]
        else:
            self._state[key] = value
        self._state['_changed'] = True

    def __delitem__(self, key):
        del self._state[key]
        self._state['_changed'] = True

    def __iter__(self):
        return self._state.iteritems()

    def __contains__(self, key):
        return key in self._state

    def control(self, key):
        if key not in self._controlled:
            self._controlled.append(key)

    def uncontrol(self, key):
        if key in self._controlled:
            self._controlled.remove(key)

    def _check_controlled(self, object):
        status = False
        objtype = type(object)
        if objtype == list or objtype == tuple:
            for obj in object:
                status |= self._check_controlled(obj)
                if status:
                    return status
        elif objtype == dict or objtype == OrderedDict:
            for key, obj in object.iteritems():
                status |= self._check_controlled(obj)
                if status:
                    return status
        else:
            if Actor in inspect.getmro(type(object)):
                status |= object.state.changed
        return status

    @property
    def changed(self):
        status = self._state['_changed']
        if status:
            return status
        for key in self._controlled:
            if key in self._state:
                status |= self._check_controlled(self._state[key])
                if status:
                    return status
        return status

    @changed.setter
    def changed(self, value):
        self._state['_changed'] = bool(value)


class Actor(object):

    def __init__(self, gui):
        self.state = State()
        self.gui = gui
        self.io = gui.io
        self.screen = gui.screen
        self.stage = gui.stage
        self.theme = self.stage.theme
        self.state['scrsize'] = self.screen.getmaxyx()[::-1]

    def _draw_tile(self, y, x, tile=' ', color=None, theme=None, win=None):
        if not win:
            win = self.screen
        if theme:
            color = theme['color']
            tile = theme['tile'] or ' '
        color = color or self.theme['default']['color']
        try:
            if type(tile) == unicode:
                win.addstr(y, x, tile.encode('UTF-8'), color)
            else:
                win.addch(y, x, tile, color)
        except:
            pass

    def check_coordinates(self, x, y):
        return None

    def draw(self):
        raise NotImplementedError('Subclasses must define this method.')


class Notification(Actor):

    def __init__(self, width, height, *args, **kwargs):
        super(Notification, self).__init__(*args, **kwargs)
        self.state['width'] = width
        self.state['height'] = height
        self.state['border_color'] = self.theme['notification']['border']['color']
        self.state['text_color'] = self.theme['notification']['text']
        self.init_win()

    def init_win(self):
        width, height = self.state[('width', 'height')]
        bcolor, tcolor = self.state[('border_color', 'text_color')]
        scrwidth, scrheight = self.state['scrsize']
        sx = scrwidth / 2 - width / 2
        sy = scrheight / 2 - height / 2
        self.win = curses.newwin(height, width, sy, sx)
        self.win.bkgd(' ', bcolor)
        self._draw_border()
        self.panel = curses.panel.new_panel(self.win)

    def _draw_border(self):
        bcolor, tcolor = self.state[('border_color', 'text_color')]
        width, height = self.state[('width', 'height')]
        border = unimap['border']['double']
        for x in range(width):
            self._draw_tile(0, x, tile=border['hline'], color=bcolor, win=self.win)
            self._draw_tile(height - 1, x, tile=border['hline'], color=bcolor, win=self.win)
        for y in range(height):
            self._draw_tile(y, 0, tile=border['vline'], color=bcolor, win=self.win)
            self._draw_tile(y, width - 1, tile=border['vline'], color=bcolor, win=self.win)
        self._draw_tile(0, 0, tile=border['ulc'], color=bcolor, win=self.win)
        self._draw_tile(0, width - 1, tile=border['urc'], color=bcolor, win=self.win)
        self._draw_tile(height - 1, 0, tile=border['dlc'], color=bcolor, win=self.win)
        self._draw_tile(height - 1, width - 1, tile=border['drc'], color=bcolor, win=self.win)

    def _resize(self, scrwidth, scrheight):
        width, height = self.state[('width', 'height')]
        sx = scrwidth / 2 - width / 2
        sy = scrheight / 2 - height / 2
        try:
            self.panel.move(sy, sx)
            self.state.changed = True
        except:
            pass

    def draw(self):
        curses.panel.update_panels()


class NotificationHelp(Notification):
    keymap = OrderedDict([
        ('ARROWS', 'Navigation'),
        ('SPACE (LMB)', 'Enable/Disable a vertex'),
        ('ENTER', 'Enable a vertex and disable all other'),
        ('A (DLMB)', 'Set amount of generated records'),
        ('S (RMB)', 'Set static value of edges'),
        ('G', 'Generate'),
        ('D', 'Delete last generated records of enabled vertexes'),
        ('SHIFT + D', 'Delete all generated records of enabled vertexes'),
        ('P', 'Purge all generated records'),
        ('ESC', 'Cancel edit mode'),
        ('Q', 'Quit'),
    ])

    def __init__(self, *args, **kwargs):
        width, height = self._calculate_size()
        super(NotificationHelp, self).__init__(width=width, height=height, *args, **kwargs)

    def _calculate_size(self):
        width, height = 0, 0
        self.max_key_len = max([len(k) for k in self.keymap.keys()])
        for key, text in self.keymap.iteritems():
            text = self._get_text(key, text)
            width = max(width, len(text))
            height += 1
        width += 6
        height += 4
        return (width, height)

    def _get_text(self, key, text):
        return key + ': ' + ' ' * (self.max_key_len - len(key)) + text

    def _draw_help(self):
        tcolor = self.state['text_color']
        color = tcolor['default']['color']
        x, y = 3, 2
        for key, text in self.keymap.iteritems():
            self.win.addstr(y, x, self._get_text(key, text), color)
            y += 1

    def draw(self):
        self._draw_help()
        super(NotificationHelp, self).draw()

class NotificationResult(Notification):

    def __init__(self, result, action, *args, **kwargs):
        width, height = self._calculate_size(result, action)
        super(NotificationResult, self).__init__(width=width, height=height, *args, **kwargs)
        self.state['result'] = result
        self.state['action'] = action

    def _calculate_size(self, result, action):
        self.max_name_len = max([len(x._meta['model'].__name__) for x in result.keys()])
        width, height = 0, 0
        for shape, data in result.iteritems():
            text = self._get_text(shape, data, action)
            data['_text'] = text 
            width = max(width, len(text))
            height += 1
        width += 6
        height += 4
        return (width, height)

    def _get_text(self, shape, data, action=None):
        if not action:
            action = self.state['action']
        name = shape._meta['model'].__name__
        name = name + ': ' + ' ' * (self.max_name_len - len(name)) 
        if action == 'gen':
            return '%s %d records generated' % (name, data['amount'])
        elif action == 'del':
            return '%s %d records deleted' % (name, data['amount'])

    def _draw_result(self):
        tcolor = self.state['text_color']
        x, y = 3, 2
        for shape, data in self.state['result'].iteritems():
            text = data['_text']
            color = tcolor[data['status']]['color']
            self.win.addstr(y, x, text, color)
            y += 1

    def draw(self):
        self._draw_result()
        super(NotificationResult, self).draw()


class InputField(Actor):

    def __init__(self, title='', text='', enter=None, esc=None, *args, **kwargs):
        super(InputField, self).__init__(*args, **kwargs)
        self.state['title'] = title
        self.state['color'] = self.theme['input']['color']
        self.init_io(text, enter, esc)

    def init_io(self, text, enter, esc):
        self.io.clean('editor')
        if enter:
            self.io.register('ENTER', enter, 'editor')
        if esc:
            self.io.register('ESC', esc, 'editor')
        self.io.change_mode('editor')
        self.io.configure_editor(text=text, color=self.state['color'])

    def draw(self):
        text = self.io.text
        color = self.state['color']
        width, height = self.state['scrsize']
        title = self.state['title']
        try:
            for x in range(width):
                self._draw_tile(height - 1, x, ' ', color)
            self.screen.addstr(height - 1, 1, title + text, color)
        except:
            pass


class TreeBorder(Actor):

    def __init__(self, *args, **kwargs):
        super(TreeBorder, self).__init__(*args, **kwargs)
        self.state['color'] = self.theme['border']['color']
        self.state['mode'] = 'static'

    def draw(self):
        color = self.state['color']
        width, height = self.state['scrsize']
        for x in xrange(width):
            self._draw_tile(0, x, color=color, tile=' ')
            self._draw_tile(height - 1, x, color=color, tile=' ')
        self.draw_text('Super DB Generator', 'up', bold=True)
        self.draw_text("Press 'H' for Help", 'down')

    def draw_text(self, text, border, bold=False):
        width, height = self.state['scrsize']
        y = [0, height - 1][border == 'down']
        if len(text) > width:
            text = text[:width]
        x = width / 2 - len(text) / 2
        color = self.state['color']
        if bold:
            color |= curses.A_BOLD
        self.screen.addstr(y, x, text, color)

    def _resize(self, width, height):
        try:
            self.screen.move(self.state['scrsize'][1] - 1, 0)
            self.screen.deleteln()
        except:
            pass
        self.state['scrsize'] = (width, height)


class Vertex(Actor):

    def __init__(self, x, y, title, shape, tree, *args, **kwargs):
        super(Vertex, self).__init__(*args, **kwargs)
        self.tree = tree
        self.state['x'] = x
        self.state['y'] = y
        self.state['title'] = title
        self.state['shape'] = shape
        self.state['width'] = len(title) + 6
        self.state['height'] = 5
        self.state['selected'] = False
        self.state['vertex_enabled'] = self.theme['vertex_enabled']
        self.state['vertex_disabled'] = self.theme['vertex_disabled']
        self.state['vertex_selected_enabled'] = self.theme['vertex_selected_enabled']
        self.state['vertex_selected_disabled'] = self.theme['vertex_selected_disabled']
        self.state['enabled'] = self.tree.is_enabled(self.state['shape'])
        self.state['ports'] = []
        lt, rt, bt, tt = curses.ACS_LTEE, curses.ACS_RTEE, curses.ACS_BTEE, curses.ACS_TTEE
        self.port_map = {'r': lt, 'l': rt,
                         'u': bt, 'd': tt}
        self.state['statics'] = []
        self.state['amount'] = None
        self.static_edges = None

    def draw_box(self, x, y, width, height, border_color, space_color=None):
        if not space_color:
            space_color = border_color

        self._draw_tile(y, x, color=border_color, tile=curses.ACS_ULCORNER)
        self._draw_tile(y, x + width - 1, color=border_color, tile=curses.ACS_URCORNER)
        self._draw_tile(y + height - 1, x, color=border_color, tile=curses.ACS_LLCORNER)
        self._draw_tile(y + height - 1, x + width - 1, color=border_color, tile=curses.ACS_LRCORNER)

        for i in [y, y + height - 1]:
            for j in range(x + 1, x + width - 1):
                self._draw_tile(i, j, color=border_color, tile=curses.ACS_HLINE)

        for i in range(y + 1, y + height - 1):
            self._draw_tile(i, x, color=border_color, tile=curses.ACS_VLINE)
            self._draw_tile(i, x + width - 1, color=border_color, tile=curses.ACS_VLINE)

        for i in range(y + 1, y + height - 1):
            for j in range(x + 1, x + width - 1):
                self._draw_tile(i, j, color=space_color, tile=' ')

    def draw(self):
        x, y, title = self.state[('x', 'y', 'title')]
        width, height = self.state[('width', 'height')]
        vertex = None
        if self.state['enabled']:
            if self.state['selected']:
                vertex = self.state['vertex_selected_enabled']
            else:
                vertex = self.state['vertex_enabled']
        else:
            if self.state['selected']:
                vertex = self.state['vertex_selected_disabled']
            else:
                vertex = self.state['vertex_disabled']
        self.draw_box(x, y, width, height, vertex['border']['color'], vertex['space']['color'])
        if len(self.state['statics']):
            try:
                self.screen.addstr(y + 1, x + 1, u'\u27c6'.encode('UTF-8'), vertex['text']['color'])
            except:
                pass

        if self.state['amount']:
            amount = str(self.state['amount'])
            l_amount = len(amount)
            try:
                amount = ''.join(map(lambda x: unimap['small'][x], amount)).encode('UTF-8')
                self.screen.addstr(y + 3, x + width / 2 - l_amount / 2, amount, vertex['text']['color'])
            except:
                pass

        for port in self.state['ports']:
            self._draw_tile(port[1][1], port[1][0], color=vertex['border']['color'], tile=self.port_map[port[0]])
        try:
            self.screen.addstr(y + 2, x + 3, title, vertex['text']['color'] | curses.A_BOLD)
        except:
            pass

    def _set_amount(self, text):
        if text:
            if text.isdigit():
                self.state['amount'] = int(text)
                self.tree.set_amount(self.state['shape'], int(text))
                self._cancel_editor()
            elif text[0].lower() == 'x' and text[1:].isdigit():
                self.state['amount'] = text[0].lower() + text[1:]
                self.tree.set_amount(self.state['shape'], self.state['amount'])
                self._cancel_editor()
        else:
            self._cancel_editor()

    def _set_statics(self, text):
        if not self.static_edges:
            self._cancel_editor()
            return
        elif len(self.static_edges) == 0:
            self._cancel_editor()
            return
        else:
            if not text:
                self.static_edges.pop(0)
            else:
                edge = self.static_edges.pop(0)
                self.state['statics'].append((edge[0], edge[1], edge[2], text))
                self.tree.set_statics(self.state['shape'], self.state['statics'])

            if len(self.static_edges):
                self._right_click(-1, -1)
            else:
                self._cancel_editor()

    def _cancel_editor(self, text=None):
        self.io.change_mode('default')
        self.stage.act.disable_input()
        self.state.changed = True
        self.static_edges = None

    def _click(self, x, y):
        if self.state['enabled']:
            self.disable()
        else:
            self.enable()

    def disable(self):
        self.tree.disable(self.state['shape'])
        self.state['enabled'] = False

    def enable(self):
        self.tree.enable(self.state['shape'])
        self.state['enabled'] = True

    def _dbl_click(self, x, y):
        self.state['amount'] = None
        self.tree.del_amount(self.state['shape'])
        title = '<%s> Number of records: ' % (self.state['title'])
        self.stage.act.enable_input(title=title, enter=self._set_amount,
                                    esc=self._cancel_editor)

    def _right_click(self, x, y):
        if not self.static_edges:
            self.state['statics'] = []
            self.tree.del_statics(self.state['shape'])
            shape = self.state['shape']
            edges = []
            for parent in self.tree.get_parents(shape):
                for edge in self.tree.get_edges(parent, shape):
                    edges.append((edge[1], edge[0], parent))
            if len(edges):
                self.static_edges = edges

        if self.static_edges:
            edge = self.static_edges[0]
            parent_name = edge[2]._meta['model'].__name__
            title = '<%s -> %s> %s = ' % (parent_name, self.state['title'], edge[0])
            self.stage.act.enable_input(title=title, enter=self._set_statics,
                                        esc=self._cancel_editor)

    def check_coordinates(self, x, y):
        mx, my = self.state['x'], self.state['y']
        w, h = self.state['width'], self.state['height']
        if x >= mx and x < mx + w:
            if y >= my and y < my + h:
                return self
        return None


class Tree(Actor):

    def __init__(self, *args, **kwargs):
        super(Tree, self).__init__(*args, **kwargs)
        self.state['edges_enabled'] = self.theme['vertex_enabled']['edges']
        self.state['edges_disabled'] = self.theme['vertex_disabled']['edges']
        self.state['selected'] = None
        self.state['vertexes'] = {'left': [], 'right': [], 'center': [], 'free': []}
        self.state.control('vertexes')
        self.initialized = False
        self.shape_map = {}
        self.tree = ShapesTree()
        self.tree.enable_all()
        self.init_consts()
        self.grow()

    def init_consts(self):
        lt, rt, bt, tt = curses.ACS_LTEE, curses.ACS_RTEE, curses.ACS_BTEE, curses.ACS_TTEE
        urc, lrc, llc, ulc = curses.ACS_URCORNER, curses.ACS_LRCORNER, curses.ACS_LLCORNER, curses.ACS_ULCORNER
        hl, vl = curses.ACS_HLINE, curses.ACS_VLINE
        self.port_map = {'r': lt, 'l': rt,
                         'u': bt, 'd': tt}
        self.corner_map = {('r', 'd'): urc, ('u', 'l'): urc,
                           ('d', 'l'): lrc, ('r', 'u'): lrc,
                           ('l', 'u'): llc, ('d', 'r'): llc,
                           ('u', 'r'): ulc, ('l', 'd'): ulc}
        self.inter_map = {(ulc, 'u'): lt, (ulc, 'l'): tt,
                          (llc, 'd'): lt, (llc, 'l'): bt,
                          (urc, 'u'): rt, (urc, 'r'): tt,
                          (lrc, 'd'): rt, (lrc, 'r'): bt,
                          (hl, ulc): tt, (hl, llc): bt,
                          (hl, urc): tt, (hl, lrc): bt,
                          (vl, ulc): lt, (vl, llc): lt,
                          (vl, urc): rt, (vl, lrc): rt,
                          (lt, 'u'): lt, (lt, 'd'): lt,
                          (lt, ulc): lt, (lt, llc): lt,
                          (rt, 'u'): rt, (rt, 'd'): rt,
                          (rt, urc): rt, (rt, lrc): rt,
                          (bt, 'l'): bt, (bt, 'r'): bt,
                          (bt, llc): bt, (bt, lrc): bt,
                          (tt, 'l'): tt, (tt, 'r'): tt,
                          (tt, ulc): tt, (tt, urc): tt,}
        self.rev_map = {lt: 'LTEE', rt: 'RTEE', bt: 'BTEE', tt: 'TTEE',
                        urc: 'URC', lrc: 'LRC', llc: 'LLC', ulc: 'ULC',
                        hl: 'HLINE', vl: 'VLINE'}

    def _create_vertex(self, object, x, y):
        title = object._meta['model'].__name__
        vertex = Vertex(gui=self.gui, x=x, y=y, title=title, shape=object, tree=self.tree)
        self.shape_map[object] = vertex
        return vertex

    def _get_widths(self, objects):
        widths = []
        for obj in objects:
            widths.append(len(obj._meta['model'].__name__) + 6)
        return widths

    def grow(self):
        center = self.tree.get_childs([UsersShape, WavesShape])
        left = [UsersShape] + self.tree.get_childs(UsersShape)
        right = [WavesShape] + self.tree.get_childs(WavesShape)
        left = filter(lambda x: x not in center and x != WavesShape, left)
        right = filter(lambda x: x not in center, right)
        free = filter(lambda x: x not in right and x not in left,
                      self.tree.get_all())
        wl = self._get_widths(left)
        wr = self._get_widths(right)
        wc = self._get_widths(center)
        mwl, mwr, mwc = max(wl), max(wr), max(wc)
        scrwidth, scrheight = self.state['scrsize']
        xl, xr = 1, scrwidth - (mwr + 1)
        xc = (mwl + xl) + ((xr - (mwl + xl)) / 2) - (mwc / 2)

        for i in range(len(left)):
            vertex = self._create_vertex(left[i], xl, i * 5 + 1)
            self.state['vertexes']['left'].append(vertex)
        for i in range(len(right)):
            vertex = self._create_vertex(right[i], xr + mwr - wr[i], i * 5 + 1)
            self.state['vertexes']['right'].append(vertex)
        for i in range(len(center)):
            vertex = self._create_vertex(center[i], xc + (mwc - wc[i]) / 2, i * 5 + 3)
            self.state['vertexes']['center'].append(vertex)

    def _resize(self, width, height):
        self.screen.erase()
        vertexes = self.state['vertexes']
        mwl = max([v.state['width'] for v in vertexes['left']])
        mwr = max([v.state['width'] for v in vertexes['right']])
        mwc = max([v.state['width'] for v in vertexes['center']])
        xl, xr = 1, width - (mwr + 1)
        xc = (mwl + xl) + ((xr - (mwl + xl)) / 2) - (mwc / 2)

        for vertex in vertexes['left']:
            vertex.state['x'] = xl
            vertex.state['ports'] = []
        for vertex in vertexes['right']:
            vertex.state['x'] = xr + mwr - vertex.state['width']
            vertex.state['ports'] = []
        for vertex in vertexes['center']:
            vertex.state['x'] = xc + (mwc - vertex.state['width']) / 2
            vertex.state['ports'] = []


    def _find_optimal_path(self, parent, child, direction=None, shift=None):
        px, py, pw = parent.state['x'], parent.state['y'], parent.state['width']
        cx, cy, cw = child.state['x'], child.state['y'], child.state['width']
        if not direction:
            if abs(px - cx) > abs(py - cy):
                if px - cx > 0:
                    direction = ('l', 'r')
                else:
                    direction = ('r', 'l')
            else:
                if py - cy > 0:
                    direction = ('u', 'd')
                else:
                    direction = ('d', 'u')

        if not shift:
            shift = (0, 0)
        ports = []
        for i in range(2):
            vertex = [parent, child][i]
            x, y, w, h = vertex.state['x'], vertex.state['y'], vertex.state['width'], vertex.state['height']
            if direction[i] == 'l':
                ports.append((direction[i], (x, y + 2 + shift[i]), vertex))
            elif direction[i] == 'r':
                ports.append((direction[i], (x + w - 1, y + 2 + shift[i]), vertex))
            elif direction[i] == 'u':
                ports.append((direction[i], ((x + (w - 1) / 2) + shift[i], y), vertex))
            elif direction[i] == 'd':
                ports.append((direction[i], ((x + (w - 1) / 2) + shift[i], y + h - 1), vertex))

        p_port, c_port = ports[0][1], ports[1][1]
        dir_map = {'l': 0, 'u': 1, 'r': 0, 'd': 1}
        anti_map = {'l': 'r', 'r': 'l', 'u': 'd', 'd': 'u'}
        so_map = {'l': 'u', 'r': 'd', 'u': 'r', 'd': 'l'}
        len_map = {'l': p_port[0] - c_port[0], 'r': c_port[0] - p_port[0],
                   'u': p_port[1] - c_port[1], 'd': c_port[1] - p_port[1]}
        path = []
        direct = (dir_map[direction[0]], dir_map[direction[1]])
        if direct[0] != direct[1]:
            path.append((direction[0], len_map[direction[0]]))
            path.append((anti_map[direction[1]], len_map[anti_map[direction[1]]]))
        else:
            if direction[0] != direction[1]:
                length = len_map[direction[0]]
                if length % 2 == 0:
                    length = (length / 2, length / 2)
                else:
                    length = (length / 2, length / 2 + 1)

                path.append((direction[0], length[0]))
                sod = so_map[direction[0]]
                if len_map[sod] > len_map[anti_map[sod]]:
                    path.append((sod, len_map[sod]))
                else:
                    path.append((anti_map[sod], len_map[anti_map[sod]]))
                path.append((direction[0], length[1]))
            else:
                length = (1, 1)
                if len_map[direction[0]] > len_map[anti_map[direction[0]]]:
                    length = (len_map[direction[0]] + 1, 1)
                else:
                    length = (1, len_map[anti_map[direction[0]]] + 1)

                path.append((direction[0], length[0]))
                sod = so_map[direction[0]]
                if len_map[sod] > len_map[anti_map[sod]]:
                    path.append((sod, len_map[sod]))
                else:
                    path.append((anti_map[sod], len_map[anti_map[sod]]))
                path.append((anti_map[direction[1]], length[1]))
        return ports, path

    def _intersection(self, x, y, color, direction, char):
        colors = [self.state['edges_enabled']['color'], self.state['edges_disabled']['color']]
        for c in colors:
            r = char & ~c
            if r >= 4194410 and r <= 4194424:
                char = r
                break
        if type(direction) != int:
            if char >= 4194410 and char <= 4194424:
                if (char, direction) in self.inter_map:
                    self._draw_tile(y, x, color=color, tile=self.inter_map[(char, direction)])
                else:
                    if direction == 'r' or direction == 'l':
                        self._draw_tile(y, x, color=color, tile=curses.ACS_HLINE)
                    else:
                        self._draw_tile(y, x, color=color, tile=curses.ACS_VLINE)
            else:
                if direction == 'r' or direction == 'l':
                    self._draw_tile(y, x, color=color, tile=curses.ACS_HLINE)
                else:
                    self._draw_tile(y, x, color=color, tile=curses.ACS_VLINE)
        else:
            if char >= 4194410 and char <= 4194424:
                if (char, direction) in self.inter_map:
                    self._draw_tile(y, x, color=color, tile=self.inter_map[(char, direction)])
                else:
                    self._draw_tile(y, x, color=color, tile=direction)
            else:
                self._draw_tile(y, x, color=color, tile=direction)


    def _draw_edge(self, ports, path, color):
        x, y = ports[0][1][0], ports[0][1][1]
        for port in ports:
            t_port = (port[0], port[1])
            if t_port not in port[2].state['ports']:
                port[2].state['ports'].append(t_port)
        ports[0][2].draw()
        ports[0][2].state.changed = False
        for j in xrange(len(path)):
            line = path[j]
            for i in xrange(line[1]):
                if line[0] == 'r':
                    x += 1
                elif line[0] == 'l':
                    x -= 1
                elif line[0] == 'u':
                    y -= 1
                elif line[0] == 'd':
                    y += 1
                flag = i != line[1] - 1
                if j != len(path) - 1:
                    flag |= path[j + 1][1] == 0
                ch = self.screen.inch(y, x)
                if flag:
                    self._intersection(x, y, color, line[0], ch)
                else:
                    if j != len(path) - 1:
                        self._intersection(x, y, color, self.corner_map[(path[j][0], path[j + 1][0])], ch)
                if not self.initialized:
                    time.sleep(0.01)
                    self.screen.refresh()


    def _equalize(self, edges, direction, reverse=False):
        index = [(0, -1), (-1, 0)][reverse]
        if direction == 'curved':
            m = 0
            for edge in edges:
                m = max(m, edge[1][index[0]][1])
            for edge in edges:
                diff = m - edge[1][index[0]][1]
                edge[1][index[0]] = (edge[1][index[0]][0], m)
                edge[1][index[1]] = (edge[1][index[1]][0], edge[1][index[1]][1] + diff)
        elif direction == 'direct-left':
            m = 9999999
            for edge in edges:
                m = min(m, edge[0][index[1]][1][0])
            for edge in edges:
                diff = edge[0][index[1]][1][0] - m + 1

                edge[1][index[0]] = (edge[1][index[0]][0], edge[1][index[0]][1] + (edge[1][index[1]][1] - diff))
                edge[1][index[1]] = (edge[1][index[1]][0], diff)
        elif direction == 'direct-right':
            m = 0
            for edge in edges:
                m = max(m, edge[0][index[1]][1][0])
            for edge in edges:
                diff = m - edge[0][index[1]][1][0] + 1

                edge[1][index[0]] = (edge[1][index[0]][0], edge[1][index[0]][1] + (edge[1][index[1]][1] - diff))
                edge[1][index[1]] = (edge[1][index[1]][0], diff)


    def _draw_group_edges(self, groupname):
        UVertex, WVertex = self.state['vertexes']['left'][0], self.state['vertexes']['right'][0]
        gmap = {'left': {'vg': 'left', 'dir': ('r', 'r'), 'shift': (1, 0), 'eq': 'curved', 'ind': 1, 'main': UVertex},
                'right': {'vg': 'right', 'dir': ('l', 'l'), 'shift': (1, 0), 'eq': 'curved', 'ind': 1, 'main': WVertex},
                'center-left': {'vg': 'center', 'dir': ('r', 'l'), 'shift': (0, 0), 'eq': 'direct-left', 'ind': 0, 'main': UVertex},
                'center-right': {'vg': 'center', 'dir': ('l', 'r'), 'shift': (0, 0), 'eq': 'direct-right', 'ind': 0, 'main': WVertex},}

        g = gmap[groupname]
        vertexes = self.state['vertexes'][g['vg']]
        edges = []
        for vertex in vertexes[g['ind']:]:
            edg = self.tree.get_edges(g['main'].state['shape'], vertex.state['shape'])
            for i in range(len(edg)):
                shift = g['shift']
                if len(edg) == 2:
                    if i % 2 == 0:
                        shift = (shift[0], shift[1] - 1)
                    else:
                        shift = (shift[0], shift[1] + 1)
                color = self.state[['edges_disabled', 'edges_enabled'][edg[i][2]]]['color']
                ports, path = self._find_optimal_path(g['main'], vertex, direction=g['dir'], shift=shift)
                edges.append((ports, path, color, vertex))
        self._equalize(edges, g['eq'])
        for edge in edges:
            self._draw_edge(edge[0], edge[1], color=edge[2])
            edge[3].draw()
            edge[3].state.changed = False
        g['main'].state.changed = False

    def disable_all(self):
        for name, group in self.state['vertexes'].iteritems():
            for vertex in group:
                vertex.disable()

    def _unselect(self):
        selected = self.state['selected']
        if selected:
            self.state['vertexes'][selected[0]][selected[1]].state['selected'] = False
            self.state['selected'] = None

    def _handle_up(self):
        selected = self.state['selected']
        new_selected = ('left', 0)
        if selected:
            row = (selected[1] - 1) % len(self.state['vertexes'][selected[0]])
            new_selected = (selected[0], row)
            self.state['vertexes'][selected[0]][selected[1]].state['selected'] = False
        self.state['vertexes'][new_selected[0]][new_selected[1]].state['selected'] = True
        self.state['selected'] = new_selected

    def _handle_down(self):
        selected = self.state['selected']
        new_selected = ('left', 0)
        if selected:
            row = (selected[1] + 1) % len(self.state['vertexes'][selected[0]])
            new_selected = (selected[0], row)
            self.state['vertexes'][selected[0]][selected[1]].state['selected'] = False
        self.state['vertexes'][new_selected[0]][new_selected[1]].state['selected'] = True
        self.state['selected'] = new_selected

    def _handle_right(self):
        circle = ['left', 'center', 'right']
        selected = self.state['selected']
        new_selected = ('left', 0)
        if selected:
            column = circle[(circle.index(selected[0]) + 1) % len(circle)]
            row = selected[1]
            if row >= len(self.state['vertexes'][column]):
                row = len(self.state['vertexes'][column]) - 1
            new_selected = (column, row)
            self.state['vertexes'][selected[0]][selected[1]].state['selected'] = False
        self.state['vertexes'][new_selected[0]][new_selected[1]].state['selected'] = True
        self.state['selected'] = new_selected

    def _handle_left(self):
        circle = ['left', 'center', 'right']
        selected = self.state['selected']
        new_selected = ('left', 0)
        if selected:
            column = circle[(circle.index(selected[0]) - 1) % len(circle)]
            row = selected[1]
            if row >= len(self.state['vertexes'][column]):
                row = len(self.state['vertexes'][column]) - 1
            new_selected = (column, row)
            self.state['vertexes'][selected[0]][selected[1]].state['selected'] = False
        self.state['vertexes'][new_selected[0]][new_selected[1]].state['selected'] = True
        self.state['selected'] = new_selected

    def _handle_space(self):
        selected = self.state['selected']
        if selected:
            vertex = self.state['vertexes'][selected[0]][selected[1]]
            vertex._click(-1, -1)
        else:
            self._handle_left()

    def _handle_enter(self):
        selected = self.state['selected']
        if selected:
            self.disable_all()
            vertex = self.state['vertexes'][selected[0]][selected[1]]
            vertex.enable()
        else:
            self._handle_left()

    def _handle_a(self):
        selected = self.state['selected']
        if selected:
            vertex = self.state['vertexes'][selected[0]][selected[1]]
            vertex._dbl_click(-1, -1)

    def _handle_s(self):
        selected = self.state['selected']
        if selected:
            vertex = self.state['vertexes'][selected[0]][selected[1]]
            vertex._right_click(-1, -1)

    def _handle_g(self):
        defaults = self.tree.set_defaults()
        if defaults:
            for shape, changes in defaults.iteritems():
                if shape in self.shape_map:
                    vertex = self.shape_map[shape]
                    for key, value in changes.iteritems():
                        vertex.state[key] = value
        else:
            result = self.tree.generate()
            if result:
                self.stage.act.show_result(result, 'gen')

    def _handle_d(self):
        result = self.tree.delete(last=True)
        if result:
            self.stage.act.show_result(result, 'del')

    def _handle_D(self):
        result = self.tree.delete(all=True)
        if result:
            self.stage.act.show_result(result, 'del')

    def _handle_p(self):
        result = self.tree.purge()
        if result:
            self.stage.act.show_result(result, 'del')

    def check_coordinates(self, x, y):
        self._unselect()
        for key, vertexes in self.state['vertexes'].iteritems():
            for vertex in vertexes:
                result = vertex.check_coordinates(x, y)
                if result:
                    return result
        return None

    def draw_edges(self):
        ml, mr = self.state['vertexes']['left'][0], self.state['vertexes']['right'][0]
        self._draw_group_edges('left')
        self._draw_group_edges('center-left')
        edge = self.tree.get_edges(ml.state['shape'], mr.state['shape'])[0]
        color = self.state[['edges_disabled', 'edges_enabled'][edge[2]]]['color']
        ports, path = self._find_optimal_path(ml, mr, direction=('r', 'l'), shift=(-1, -1))
        self._draw_edge(ports, path, color)
        self._draw_group_edges('right')
        self._draw_group_edges('center-right')

    def draw(self):
        self.draw_edges()
        self.initialized = True


class Act(object):

    def __init__(self, gui):
        self.actors = OrderedDict()
        self.gui = gui
        self.screen = gui.screen
        self.theme = gui.stage.theme
        self.init_mouse_map()
        self.io = gui.io
        self.io.clean()
        self.io.register('_MOUSE_EVENT', self.mouse_events)

    def init_mouse_map(self):
        self.mouse_map = {curses.BUTTON1_CLICKED: '_click',
                          curses.BUTTON1_DOUBLE_CLICKED: '_dbl_click',
                          curses.BUTTON3_CLICKED: '_right_click',
                          curses.BUTTON3_DOUBLE_CLICKED: '_dbl_right_click'}

    def _register_keys(self):
        raise NotImplementedError('Subclasses must define this method.')

    def _set_background(self, color, tile=' '):
        self.screen.bkgd(tile, color)

    def _get_actors(self, object=None):
        if not object:
            object = self.actors
        actors = []
        objtype = type(object)
        if objtype == list or objtype == tuple:
            for obj in object:
                actors += self._get_actors(obj)
        elif objtype == dict or objtype == OrderedDict:
            for key, obj in object.iteritems():
                actors += self._get_actors(obj)
        else:
            actors.append(object)
        return actors

    def _draw_all(self, actors=None):
        if not actors:
            actors = self._get_actors()
        for actor in actors:
            actor.draw()
            actor.state.changed = False

    def _check_all(self, actors=None):
        if not actors:
            actors = self._get_actors()
        status = False
        for actor in actors:
            status |= actor.state.changed
            if status:
                break
        return status

    def _find_clicked_actors(self, x, y, actors=None):
        if not actors:
            actors = self._get_actors()
        clicked = []
        for actor in actors:
            obj = actor.check_coordinates(x, y)
            if obj:
                if type(obj) == list or type(obj) == tuple:
                    clicked += list(obj)
                else:
                    clicked.append(obj)
        return clicked

    def mouse_events(self, x, y, button):
        actors = self._find_clicked_actors(x, y)
        if button in self.mouse_map:
            funcname = self.mouse_map[button]
            for actor in actors:
                func = getattr(actor, funcname, None)
                if func:
                    func(x, y)

    def draw(self, force=False):
        actors = self._get_actors()
        if force or self._check_all(actors=actors):
            self._draw_all(actors=actors)
            self.screen.refresh()


class TreeAct(Act):

    def __init__(self, *args, **kwargs):
        super(TreeAct, self).__init__(*args, **kwargs)
        self._set_background(self.theme['bg']['color'])
        self.hire_actors()
        self._register_keys()

    def _register_keys(self):
        tree = self.actors['tree']
        self.io.register(ord('q'), self.gui.quit)
        self.io.register('UP', tree._handle_up)
        self.io.register('DOWN', tree._handle_down)
        self.io.register('LEFT', tree._handle_left)
        self.io.register('RIGHT', tree._handle_right)
        self.io.register('SPACE', tree._handle_space)
        self.io.register(ord('a'), tree._handle_a)
        self.io.register(ord('s'), tree._handle_s)
        self.io.register(ord('g'), tree._handle_g)
        self.io.register('ENTER', tree._handle_enter)
        self.io.register(ord('d'), tree._handle_d)
        self.io.register(ord('D'), tree._handle_D)
        self.io.register(ord('p'), tree._handle_p)
        self.io.register('RESIZE', self.resize)
        self.io.register(ord('h'), self.show_help)
        self.io.register('_ANY', self.hide_notification, 'notification')

    def hire_actors(self):
        self.actors['border'] = TreeBorder(gui=self.gui)
        self.actors['tree'] = Tree(gui=self.gui)

    def enable_input(self, title='', text='', enter=None, esc=None):
        self.actors['input'] = InputField(gui=self.gui, title=title, text=text,
                                          enter=enter, esc=esc)

    def disable_input(self):
        self.actors.pop('input', None)

    def show_help(self):
        self.actors['notification'] = NotificationHelp(gui=self.gui)
        self.io.change_mode('notification')

    def show_result(self, result, action):
        self.actors['notification'] = NotificationResult(gui=self.gui, result=result, action=action)
        self.io.change_mode('notification')

    def hide_notification(self, key=None):
        self.actors.pop('notification', None)
        self.io.change_mode('default')

    def resize(self):
        width, height = self.screen.getmaxyx()[::-1]
        actors = self._get_actors()
        for actor in actors:
            func = getattr(actor, '_resize', None)
            if func:
                func(width, height)


class Stage(object):

    def __init__(self, gui):
        self.theme = None
        self.act = None
        self.gui = gui
        self.screen = gui.screen
        self.io = gui.io
        self.theme = Theme(themes)
        self.theme.pick('default')

    def change_act(self, act):
        self.act = act(gui=self.gui)

    def update(self):
        self.act.draw()


class GUI(object):
    active = True
    fps = 15

    def __init__(self, screen):
        self.screen = screen
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        curses.start_color()
        self.screen.keypad(1)
        self.screen.leaveok(0)
        curses.mousemask(-1)

        self.screen.timeout(1000 / ((self.fps - 1) or 1))
        self.io = IO(self)
        self.stage = Stage(self)
        self.stage.change_act(TreeAct)

    def update(self):
        self.io.react()
        self.stage.update()

    def loop(self):
        frame_len = 1.0 / self.fps
        last_update = time.time() - frame_len * 2
        while self.active:
            cur_time = time.time()
            if cur_time - last_update >= frame_len:
                self.update()
                last_update = cur_time
            else:
                time.sleep((frame_len - cur_time - last_update) * 1000)

    def start(self):
        self.loop()

    def quit(self):
        self.active = False
        self.screen.clear()
        self.screen.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()


def main(screen):
    gui = GUI(screen=screen)
    gui.start()
    gui.quit()


if __name__ == '__main__':
    curses.wrapper(main)
