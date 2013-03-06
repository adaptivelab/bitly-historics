from matplotlib import cbook

# Attribution:
# http://stackoverflow.com/users/325565/joe-kington
# http://stackoverflow.com/a/4674445/18688
# may be related also:
# http://matplotlib.org/examples/pylab_examples/cursor_demo.html (but not
# tested)

class DataCursor(object):
    """A simple data cursor widget that displays the x,y location of a
    matplotlib artist when it is selected."""
    def __init__(self, artists, tolerance=5, offsets=(-20, 20),
                 template='x: %0.2f\ny: %0.2f', display_all=False):
        """Create the data cursor and connect it to the relevant figure.
        "artists" is the matplotlib artist or sequence of artists that will be
            selected.
        "tolerance" is the radius (in points) that the mouse click must be
            within to select the artist.
        "offsets" is a tuple of (x,y) offsets in points from the selected
            point to the displayed annotation box
        "template" is the format string to be used. Note: For compatibility
            with older versions of python, this uses the old-style (%)
            formatting specification.
        "display_all" controls whether more than one annotation box will
            be shown if there are multiple axes.  Only one will be shown
            per-axis, regardless.
        """
        self.template = template
        self.offsets = offsets
        self.display_all = display_all
        if not cbook.iterable(artists):
            artists = [artists]
        self.artists = artists
        self.axes = tuple(set(art.axes for art in self.artists))
        self.figures = tuple(set(ax.figure for ax in self.axes))

        self.annotations = {}
        for ax in self.axes:
            self.annotations[ax] = self.annotate(ax)

        for artist in self.artists:
            artist.set_picker(tolerance)
            #import pdb; pdb.set_trace()
        for fig in self.figures:
            fig.canvas.mpl_connect('pick_event', self)

    def annotate(self, ax):
        """Draws and hides the annotation box for the given axis "ax"."""
        annotation = ax.annotate(self.template, xy=(0, 0), ha='right',
                                 xytext=self.offsets, textcoords='offset points', va='bottom',
                                 bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                                 arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
                                 )
        annotation.set_visible(False)
        return annotation

    def __call__(self, event):
        """Intended to be called through "mpl_connect"."""
        # Rather than trying to interpolate, just display the clicked coords
        # This will only be called if it's within "tolerance", anyway.
        x, y = event.mouseevent.xdata, event.mouseevent.ydata
        annotation = self.annotations[event.artist.axes]
        #import pdb; pdb.set_trace()
        if x is not None:
            if not self.display_all:
                # Hide any other annotation boxes...
                for ann in self.annotations.values():
                    ann.set_visible(False)
            # Update the annotation in the current axis..
            annotation.xy = x, y
            #annotation.set_text(event.artist.get_label() + "" + self.template % (x, y))
            label = event.artist.get_label() + "\nx: {} y: {}".format(x, y)
            print label
            annotation.set_text(label)
            annotation.set_visible(True)
            event.canvas.draw()

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    plt.figure()
    plt.subplot(2, 1, 1)
    line1, = plt.plot(range(10), 'ro-')
    plt.subplot(2, 1, 2)
    line2, = plt.plot(range(10), 'bo-')

    DataCursor([line1, line2])

    plt.show()
