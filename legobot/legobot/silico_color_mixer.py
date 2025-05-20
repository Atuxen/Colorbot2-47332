import numpy as np


class SilicoColorMixer(object):
    """
    An in silico mirror of the LEGO robot control class

    Simulates mixing of colored liquids into cuvettes
    """

    # https://www.rapidtables.com/web/color/RGB_Color.html
    default_color_codes = {'yellow_t': [249, 242, 30],
                           'red_t': [220, 35, 40],
                           'blue_t': [54, 59, 212],
                           'green_t': [73, 213, 5],
                           'red_u': [220, 35, 40],
                           'yellow_u': [249, 242, 30],
                           'green_u': [73, 213, 5],
                           'purple_u': [214, 39, 249],
                           }

    def __init__(self, noise={'colors': 1, 'volume': 0.02, 'measurement': 2},
                 colors=['red_t', 'green_t', 'blue_t', 'yellow_t'],
                 color_codes=None,
                 target=None):
        """A lego robot control class for in silico exercise. Simulates mixing of colored liquids into cuvettes.

        Args:
            noise (dict, optional): All noise is gaussian distributed with mean 0 and std specified by value. 
            colors (list, optional): List containing the colors available to the mixer in the desired order
                Possible colors: 'red_t', 'green_t', 'blue_t', 'yellow_t', 'red_u', 'yellow_u', 'green_u', 'purple_u' 
            color_codes (dict, optional):  Can manually specify color codes for colors not in color_codes()
                function or overrule defaults values
                {'purple': [125, 30, 249],  # Not in defaults
                'red_t': [249, 30, 52]}  # Overrules default value
            target (tuple, optional): A tuple of the optimized value in the (r,g,b) format you wish to optimize to. 
                Used in run_cuvette().
        """
        self.noise = noise
        self.colors = colors
        color_codes = color_codes or {}
        self.default_color_codes.update(color_codes)
        self.color_codes = self.default_color_codes
        color_codes_matrix0 = color_codes_matrix(self.colors,
                                                 self.color_codes)
        self.color_codes_matrix = color_codes_matrix0.copy()
        self.target = target

    def run_cuvette(self, color_list, read_target=False):
        """
        Function that simulates mixing liquids in a cuvette and reading the
        output color

        color_list: [v_liq1, v_liq2, ...]
           list of liquid volumes to mix
           Will be normalized. Thus:
               run_cuvette([1., 1.]) = run_cuvette([0.3, 0.3])
        """
        assert len(self.colors) == len(color_list)
        norm_color_list0 = normalize(color_list, norm=3.0)

        if self.noise:
            color_list = add_noise(norm_color_list0, self.noise['volume'],
                                   n_min=0.)
        norm_color_list = normalize(color_list)

        if self.noise:
            ccode_matrix = add_noise(self.color_codes_matrix,
                                     self.noise['colors'],
                                     integer=True,
                                     n_min=0, n_max=255)
        else:
            ccode_matrix = self.color_codes_matrix

        mixed_color = np.asarray(np.dot(norm_color_list, ccode_matrix))
        if self.noise:
            mixed_color = add_noise(mixed_color,
                                    self.noise['measurement'],
                                    integer=True, n_min=0, n_max=255)
        if read_target:
            return tuple(mixed_color), self.target
        else:
            return tuple(mixed_color)

    def get_colors(self):
        """Returns the used colors and their color codes"""
        return self.colors, self.color_codes_matrix


def add_noise(input_list0, noise, integer=False, n_max=False, n_min=False):
    """
    Adds normally distributed noise to a list or multidimensional array
    Noise is added elementwise

    input_list: list or multidimensional array
    noise: float or int
        The standard deviation of the noise
    integer: bool
        If True the output contains integers. Otherwise output is floats
    n_max, n_min: False, int, or float
        Not used if False. Changes value to n_min if below and n_max if above
    """

    # Prevent input list from being modified
    input_list = input_list0.copy()
    # Do not add noise to values that are 0.
    non_zero = np.where(np.asarray(input_list) > 0.0, 1, 0)
    input_list = np.asarray(input_list, dtype=float)
    input_list += noise * np.random.normal(size=input_list.shape) * non_zero
    # input_list += noise * np.random.normal(size=input_list.shape)
    if n_min is not False:
        input_list[input_list < n_min] = n_min
    if n_max:
        input_list[input_list > n_max] = n_max
    if integer:
        input_list = np.around(input_list)
        input_list.astype(int)

    return input_list


def normalize(input_list, norm=1.0):
    """
    Normalizes the input color ratios to sum = norm
    """
    return [float(i) * norm / sum(input_list) for i in input_list]


def color_codes_matrix(colors, color_codes):
    """
    Specifies builds color code matrix

    colors: list of strings
        The names of the colors you you wish to use in the correct order
    color_codes: dict
        Dictonary containing the colors with their rgb color code in [0,255]
        format
            E.g. {'yellow': [249, 242, 30],
                  'red': [220, 35, 40],
                  'blue': [54, 59, 212],
                  'green': [73, 213, 5]}
    """

    ccode_matrix = np.empty((0, 3))
    for color in colors:
        ccode_matrix = np.concatenate((ccode_matrix,
                                       [color_codes[color]]),
                                      axis=0)
    return ccode_matrix


def convert_rgb_to_tuple(rgb):
    """
    Converts a rgb list or numpy array with values in [0, 255] to a tuple with
    values in [0., 1.]
    """
    return tuple([rgb_val / 255 for rgb_val in rgb])
