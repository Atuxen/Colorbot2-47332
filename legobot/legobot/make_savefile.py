# Makes a pickl save file for use in Dragonfly
import pickle
from numpy import array


def make_dragonfly_save_file(input_data, filename, constraints):
    """
    Makes a pickl file in the right save file format for use in Dragonfly

    input_data: array
        array with results obtained previously
        [[x0, y0, z0, score0],
         [x1, y1, z1, score1]]
    filename: string
        The name you want for the save file
    constraints: array
        array with constraints for x ,y z,
        [[x_min, x_max],[y_min, y_max],[z_min, z_max]]
    """

    output = {}
    # input_data = [[[1., 2.], 3.], [[4., 5.], 6.]]
    # constraints = [[0., 5.], [0., 10.]]

    input_data0 = array(input_data.copy())

    for dims in range(len(constraints)):
        scale = constraints[dims][1] - constraints[dims][0]
        input_data0[:, dims] = input_data0[:, dims] / scale

    # print(input_data0)
    points_list = []
    for data in input_data0:
        # print(data[:-1])
        points_list.append(array(data[:-1]))

    output['points'] = points_list
    true_vals = -input_data0[:, -1]
    output['true_vals'] = true_vals
    output['vals'] = true_vals

    with open(filename, 'wb') as handle:
        pickle.dump(output, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return


# python -mpickle simple2D_savefile_test
