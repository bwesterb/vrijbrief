import curses

CP_WHITE = 1
CP_BLUE = 2

class Widget(object):
    def __init__(self):
        self.touched = False
        self.window = None

    def setup(self, window):
        if self.window is not None:
            raise RuntimeError("Already setup")
        self.window = window
        self.touch()

    def touch(self):
        self.touched = True

    def update(self, forceRedraw):
        if not forceRedraw and not self.touched:
            return
        self.touched = False
        self.window.clear()
        self.do_update()
        self.window.noutrefresh()

    def do_update(self):
        raise NotImplementedError
    
    def reposition(self, x, y, w, h):
        self.window.resize(h, w)
        self.window.mvwin(y, x)

class StatusWidget(Widget):
    def __init__(self):
        super(StatusWidget, self).__init__()
        self.text = ''

    def set(self, text):
        self.text = text
        self.touch()

    def do_update(self):
        h, w = self.window.getmaxyx()
        self.window.addstr(0, 0, self.text[:w])

class PickerWidget(Widget):
    def __init__(self):
        super(PickerWidget, self).__init__()
        self.cursor = 0
        self.options = map(str, range(10))

    def do_update(self):
        h, w = self.window.getmaxyx()
        offset = max(min(self.cursor - h/2, len(self.options) - h), 0)
        for i in xrange(h):
            dabadi = False
            if offset + i < len(self.options):
                row_text = self.options[offset + i]
            else:
                dabadi = True
                row_text = '~'
            highlighted = offset + i == self.cursor
            if dabadi:
                self.window.attron(curses.color_pair(CP_BLUE))
            if highlighted:
                self.window.attron(curses.color_pair(CP_WHITE))
            try:
                self.window.addstr(i, 0, row_text[:w].ljust(w, ' '))
            except curses.error as e:
                if i != h - 1:
                    raise e
            if highlighted:
                self.window.attroff(curses.color_pair(CP_WHITE))
            if dabadi:
                self.window.attroff(curses.color_pair(CP_BLUE))

    def scroll(self, amount):
        self.cursor += amount
        if self.cursor < 0:
            self.cursor = 0
        if self.cursor >= len(self.options):
            self.cursor = len(self.options) - 1
        self.touch()

class VrijbriefCursesUI(object):
    def __init__(self):
        self.status = StatusWidget()
        self.picker = PickerWidget()

    def run(self):
        curses.wrapper(self._inside_curses)

    def _inside_curses(self, window):
        self._setup(window)
        self.update(False)
        self._main_loop()

    def _setup(self, window):
        self.window = window
        curses.use_default_colors()
        curses.init_pair(CP_WHITE, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(CP_BLUE, curses.COLOR_BLUE, -1)
        h, w = self.window.getmaxyx()
        self.picker.setup(self.window.derwin(h-1, w, 0, 0))
        self.status.setup(self.window.derwin(1, w-1, h-1, 0))

    def _main_loop(self):
        while True:
            forceRedraw = False
            try:
                k = self.window.getch()
            except KeyboardInterrupt:
                break

            h, w = self.window.getmaxyx()

            # Figure out what to do with the keypress
            if k == -1:
                continue
            elif k == 24: # ctrl-x
                break
            elif k == 10: # enter
                self.status.set('Choose %s' % self.picker.options[self.picker.cursor])
            elif k == 258: # arrow down
                self.picker.scroll(1)
            elif k == 259: # arrow up
                self.picker.scroll(-1)
            elif k == 338: # page down
                self.picker.scroll(h/2)
            elif k == 339: # page down
                self.picker.scroll(-h/2)
            elif k == 410: # redraw
                # Yes, that's right, we're not allowed to write to the bottom
                # right cell.  That is because on the old-school ones --- not
                # those virtual ones we're using now --- a write triggered
                # scrolling by one line.
                self.status.reposition(0, h-1, w-1, 1)
                self.picker.reposition(0, 0, w, h-1)
                forceRedraw = True
            else:
                self.status.set('Unknown key: %s.  Press Ctrl+x to quit.' % k)
            self.update(forceRedraw)

    def update(self, forceRedraw):
        self.status.update(forceRedraw)
        self.picker.update(forceRedraw)
        curses.doupdate()

if __name__ == '__main__':
    ui = VrijbriefCursesUI()
    ui.run()
