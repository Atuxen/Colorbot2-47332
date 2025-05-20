import numpy as np


def remove_duplicate_labels(ax, loc='lower right'):
    handles, labels = ax.get_legend_handles_labels()
    use_labels = []
    use_handles = []
    for j, l in enumerate(labels):
        if l not in use_labels:
            use_labels.append(l)
            use_handles.append(handles[j])
    ul, uh = zip(*sorted(zip(use_labels, use_handles)))
    ax.legend(uh, ul, numpoints=1, loc=loc)


def plot_interactive(ax, evaluations, no_found_candidates):
    fig = ax.get_figure()
    if len(ax.lines) == 0:
        # No lines are drawn
        ax.plot(evaluations, no_found_candidates, 'bo', label='GA')
    else:
        # Update the found candidates
        # We assume that the GA data is the first line
        xdata = ax.lines[0].get_xdata()
        ydata = ax.lines[0].get_ydata()
        xdata = np.append(xdata, evaluations)
        ydata = np.append(ydata, no_found_candidates)
        ax.lines[0].set_data(xdata, ydata)
    fig.canvas.draw()
