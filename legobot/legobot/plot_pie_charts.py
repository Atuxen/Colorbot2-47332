import numpy as np
import matplotlib.pyplot as plt


def convert_rgb_to_tuple(rgb):
    """
    Converts a rgb list or numpy array with values in [0, 255] to a tuple with
    values in [0., 1.]
    """
    return tuple([rgb_val / 255 for rgb_val in rgb])


def ratios_normalized(point, points):
    ratios = points[point]['ratios_pie']
    return [1 / sum(ratios) * i for i in ratios]


def make_piechart_plot(points0, colors='default'):
    """
    Plots the "score" as function of sample number (given by index in input
    list). Points are pie charts showing the mixing colors.
    Note that this function only works with 4 colors being mixed

    points0: list
        format: [[score1, [vol1_col1, vol1_col2, vol1_col3, vol1_col4]],
                 [score2, [vol2_col1, vol2_col2, vol2_col3, vol2_col4]],
                 ...
                 [scoreN, [volN_col1, volN_col2, volN_col3, volN_col4]],
                 ]
        score is a float value given to the point
        volX_colY is the volume of color Y used in sample X.
    colors: list
        format: [[r_col1, g_col1, b_col1],
                 [r_col2, g_col2, b_col2],
                 [r_col3, g_col3, b_col3],
                 [r_col4, g_col4, b_col4],
                ]
        r_colX, g_colX, b_colX are the r, g, b values of color X

    """
    if str(colors) == 'default':
        colors = [[220, 35, 40.],
                  [73., 213., 5.],
                  [54., 59., 212.],
                  [249., 242., 30.]]

    fig, ax = plt.subplots()
    size = 600

    points = {}
    for idx, point0 in enumerate(points0):
        points[f'point{idx+1}'] = {'x': idx + 1,
                                   'y': point0[0], 'ratios_pie': point0[1]}
    # print(points)

    def markers_out(point, points):
        """
        Function that makes the markers
        Takes in list of list with [r,g,b,y] ratios
        outputs two matrices
        """
        # print(points)
        ratio_list = ratios_normalized(point, points)
        r1 = ratio_list[0]
        r2 = r1 + ratio_list[1]
        r3 = r2 + ratio_list[2]
        x = [0] + np.cos(np.linspace(0, 2 * np.pi * r1, 10)).tolist()
        y = [0] + np.sin(np.linspace(0, 2 * np.pi * r1, 10)).tolist()
        points[point]['xy1'] = np.column_stack([x, y])
        points[point]['s1'] = np.abs(points[point]['xy1']).max()
        x = [0] + np.cos(np.linspace(2 * np.pi * r1,
                         2 * np.pi * r2, 10)).tolist()
        y = [0] + np.sin(np.linspace(2 * np.pi * r1,
                         2 * np.pi * r2, 10)).tolist()
        points[point]['xy2'] = np.column_stack([x, y])
        points[point]['s2'] = np.abs(points[point]['xy2']).max()
        x = [0] + np.cos(np.linspace(2 * np.pi * r2,
                         2 * np.pi * r3, 10)).tolist()
        y = [0] + np.sin(np.linspace(2 * np.pi * r2,
                         2 * np.pi * r3, 10)).tolist()
        points[point]['xy3'] = np.column_stack([x, y])
        points[point]['s3'] = np.abs(points[point]['xy3']).max()
        x = [0] + np.cos(np.linspace(2 * np.pi * r3, 2 * np.pi, 10)).tolist()
        y = [0] + np.sin(np.linspace(2 * np.pi * r3, 2 * np.pi, 10)).tolist()
        points[point]['xy4'] = np.column_stack([x, y])
        points[point]['s4'] = np.abs(points[point]['xy4']).max()

    def plot_the_point(point, colors):
        x_point = points[point]['x']
        y_point = points[point]['y']
        ax.scatter(x_point, y_point, marker=points[point]['xy1'],
                   s=points[point]['s1'] ** 2 * size, facecolor=convert_rgb_to_tuple(colors[0]))
        ax.scatter(x_point, y_point, marker=points[point]['xy2'],
                   s=points[point]['s2'] ** 2 * size, facecolor=convert_rgb_to_tuple(colors[1]))
        ax.scatter(x_point, y_point, marker=points[point]['xy3'],
                   s=points[point]['s3'] ** 2 * size, facecolor=convert_rgb_to_tuple(colors[2]))
        ax.scatter(x_point, y_point, marker=points[point]['xy4'],
                   s=points[point]['s4'] ** 2 * size, facecolor=convert_rgb_to_tuple(colors[3]))

    for point in points:
        markers_out(point, points)
        plot_the_point(point, colors)

    plt.xlabel("Data #")
    plt.ylabel("Score")
    plt.yscale('log')

    plt.show()
