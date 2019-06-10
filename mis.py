import warnings
import numpy as np
import os
from scipy.ndimage import shift
import psutil
import warnings

import h5py

from det_chan import return_det
from h5 import h5grab_data, h5set_attr, h5read_attr


def order_dir(path):
    """For a selected path return the ordered filenames.
    Meant for ordering images inside of a folder

    Parameters
    ==========

    path (str)
        the path to the folder you would like to order the contence of

    Returns
    =======
    the full image location, just the image name
    """
    images = sorted(os.listdir(path))
    im_loc = []
    im_name = []
    for i in images:
        im_loc.append(path+'/'+i)
        im_name.append(i)
    return im_loc, im_name

        
def zfill_scan(scan_list, fill_num):
    """Change int to str and fill them with the user set number of zeros

    Parameters
    ==========

    scan_list (str):
        a list string of the scans the user would like to import

    fill_num (int):
        the amount of numbers each number should have. fill_num=4 turns '40' into '0040'

    Returns
    =======
    A list of scan numbers with corrected zfill values
    """
    new_scan = []
    for scan in scan_list:
        new_scan.append(scan.zfill(fill_num))
    return new_scan

    
def create_file(file):
    """Create an hdf5 file

    Parameters
    ==========

    file (str)
        the path of the hdf5 file the user would like to create

    Returns
    =======
    Nothing
    """
    if (os.path.isfile(file)):
        pass
    else:
        f = open(file, 'w+')
        f.close()


def delimeter_func(string):
    """The delimeter function used in the image importer
    Used to just get the number of the image inside of the image files

    Parameters
    ==========

    string (str):
        the string the user wants to place the delimeter function on

    Returns
    =======
    a cropped string based on the delimeter function
    """
    return string.split('_')[-1][0:-4]


def tif_separation(string, func=delimeter_func):
    """Seperating the image number from the full name stored in the images folder

    Parameters
    ==========

    string (str):
        the string the user wants to place the delimeter function on

    func (function):
        the delimeter function for the string. Makes it easier to change in later versions

    Returns
    =======
    the image string name of just the number
    """
    return func(string)


def figure_size_finder(images):
    """Determine the size of the imported diffraction images

    Parameters
    ==========

    images (nd.array):
        the numpy array of the images to take the dimensions of

    Returns
    =======
    the image dimensions
    """
    im_shape = np.shape(images)
    im_len = len(im_shape)
    if im_len <= 2:
        return 1
    else:
        start_values = np.arange(1, 10)
        starting_idx = np.where(np.arange(1, 10)**2 >= len(images))[0][0]
        starting = start_values[starting_idx]
        return starting


def scan_num_convert(scan_numbers, fill_num=4):
    """Convert the users int scan numbers into strings

    Parameters
    ==========

    scan_numbers (str or int):
        takes an array of str values or int values and zfills them accordingly
    fill_num (int):
        the string fill number the user would like to use

    Returns
    =======
    the scan numbers in an array of strings with the user selected fill number
    """
    if isinstance(scan_numbers[0], str):
        scan_numbers = [int(scan) for scan in scan_numbers]
    elif isinstance(scan_numbers[0], int):
        scan_numbers = [str(scan) for scan in scan_numbers]
        scan_numbers = zfill_scan(scan_numbers, fill_num=fill_num)
    return scan_numbers


def shape_check(self):
    """Check to see if the imported hybrids have the same shape

    Parameters
    ==========

    self (SXDMFrameset)
        the sxdmframeset used

    Returns
    =======
    Nothing. Prints Important Data
    """
    try:
        hybrid_x = return_det(self.file, self.scan_numbers, group='hybrid_x')[0]
        hybrid_y = return_det(self.file, self.scan_numbers, group='hybrid_y')[0]

        shape_hybrid_x = np.shape(hybrid_x)
        shape_hybrid_y = np.shape(hybrid_y)

        len_x = len(shape_hybrid_x)
        len_y = len(shape_hybrid_y)

        if len_x != 3 and len_y != 3:
            warnings.warn('Scan Shapes Are Not The Same!')
            self.shape_checker = False
        else:
            self.shape_checker = True
            print('Hybrid Scan Shapes Are Equivalent')
    except Exception as ex:
        print('shape_check', ex)
        warnings.warn('Cannot Check Shape. Some .mda Files Might Be Missing...')


def val_check(array, resolution):
    """Check the resolution of the x and y dimensions of the scans

    Parameters
    ==========
    array (nd.array)
        array of all the scan x or y dimensions

    resolution (float)
        a numbers in um that sets the resolution check of the x and y dimensions

    Returns
    =======
    bool (True or False) on whether or not the scan dimensions are within the set resolution
    """
    min_res = array[0] - resolution
    max_res = array[0] + resolution
    output = []
    for value in array:
        if min_res <= value <= max_res:
            output.append(True)
        else:
            output.append(False)

    return all(output)


def resolution_check(self, user_resolution_um=0.0005):
    """Check if all X dimensions for all scans are equal to each other.
    Also checks in all y dimensions for all scans are equal to each other.
    Then checks if the x and y are equal to one another.

    Parameters
    ==========
    self (SXDMFramset)
        the sxdmframset

    user_resolution_um (float)
        the resolution in um the user would like the scan dimensions for

    Returns
    =======
    Nothing - sets resolution values
    """
    try:
        hybrid_x = return_det(self.file, self.scan_numbers, group='hybrid_x')[0]
        hybrid_y = return_det(self.file, self.scan_numbers, group='hybrid_y')[0]

        shape_hybrid_x = np.asarray([np.shape(scan) for scan in hybrid_x]) - [1, 1]
        shape_hybrid_y = np.asarray([np.shape(scan) for scan in hybrid_y]) - [1, 1]

        max_x = np.asarray([np.max(scan, axis=(0, 1)) for scan in hybrid_x])
        min_x = np.asarray([np.min(scan, axis=(0, 1)) for scan in hybrid_x])

        max_y = np.asarray([np.max(scan, axis=(0, 1)) for scan in hybrid_y])
        min_y = np.asarray([np.min(scan, axis=(0, 1)) for scan in hybrid_y])

        dif_x = max_x - min_x
        dif_y = max_y - min_y

        res_x = []
        res_y = []

        for i, value in enumerate(dif_x):
            len_hybrid_x = shape_hybrid_x[i][1]
            len_hybrid_y = shape_hybrid_y[i][0]
            current_x = dif_x[i]
            current_y = dif_y[i]
            res_x.append(current_x / len_hybrid_x)
            res_y.append(current_y / len_hybrid_y)

        dif_res_x = [res_x[0] - step for step in res_x]
        dif_res_y = [res_y[0] - step for step in res_y]


        validation_x = val_check(dif_res_x, user_resolution_um)
        validation_y = val_check(dif_res_y, user_resolution_um)

        print('Pixel X Dimension: {}nm\nPixel Y Dimension: {}nm'.format(np.median(res_x) * 1000,
                                                                        np.median(res_y) * 1000))
        # Store values for testing code
        self.res_x = np.median(res_x) * 1000
        self.res_y = np.median(res_y) * 1000
        self.all_res_x = res_x
        self.all_res_y = res_y
        self.validation_x = validation_x
        self.validation_y = validation_y

        if validation_x == True and validation_y == True:
            print('All X and All Y Resolutions are within ' +
                  str(user_resolution_um * 1000) + ' nanometers from each other respectivley')
        else:
            if validation_x != True and validation_y != True:
                warnings.warn('Resolution in X and Y Differ Between Scans')
            elif validation_x == True and validation_y != True:
                warnings.warn('Resolution in Y Differ Between Scans')
            elif validation_x != True and validation_y == True:
                warnings.warn('Resolution in X Differ Between Scans')

        res_difference = abs(self.res_x - self.res_y) <= (user_resolution_um * 1000)
        if res_difference == True:
            print('X And Y Resolutions Are Within {} nm Of Each Other'.format(user_resolution_um * 1000))
        elif res_difference == False:
            warnings.warn('X And Y Resolutions Are NOT Within {} nm Of Each Other\n'
                          'Plots will need to be corrected'.format(user_resolution_um * 1000))

    except Exception as ex:
        print('mis.py/resolution_check', ex)
        warnings.warn('Cannot Check Resolution. Some .mda Files Might Be Missing...')


def image_numbers(self):
    """Grab the image numbers

    Parameters
    ==========
    self (SXDMFrameset)
        the sxdmframset

    Returns
    =======
    all of the diffraction image numbers for each scan in a 3D matrix
    """
    filenumbers = return_det(self.file, self.scan_numbers, group='filenumber')[0]
    int_filenumbers = {}
    for i, scan in enumerate(filenumbers):
        int_filenumbers[self.scan_numbers[i]] = np.asarray(scan).astype(int)

    return int_filenumbers


def dic2array(dic):
    """Turn a dictionary into a numpy array

    Parameters
    ==========
    dic (dictionary)
        a dictionary of form {0: (num1, num2), 1: (num3, num4)}

    Returns
    =======
    a numpy array of form [(num1, num2), (num3, num4)]
    """
    output_array = []
    for val in dic:
        output_array.append(dic[val])
    return output_array


def array2dic(array):
    """Turn a numpy array into a dictionary

    Parameters
    ==========
    array (numpy array)
        a numpy array of form [(num1, num2), (num3, num4)] that will be turned into a dictionary

    Returns
    =======
    a dictionary of form {0: (num1, num2), 1: (num3, num4)}
    """
    new_dic = {}
    for i, dot in enumerate(array):
        new_dic[i] = (dot[0], dot[1])
    return new_dic


def array_shift(self, arrays2shift, centering_idx):
    """Translate a 3D stack of numpy arrays to align based on set centering values

    Parameters
    ==========
    self (SXDMFrameset)
        the sxdmframeset
    arrays2shift (numpy array)
        the 3 dimensional array the user wants to center around one of the indexes
    centering_idx (numpy array)
        the dxdy values (translation values) for each matrix in the array

    Returns
    =======
    the shifted array based on the dxdy values
    """
    complete_array = array2dic(h5grab_data(self.file, self.dataset_name + '/dxdy'))
    center = complete_array[centering_idx]
    center_x = center[0]
    center_y = center[1]
    translation_array = {}
    for array in complete_array:
        translation_array[array] = (center_x - complete_array[array][0], center_y - complete_array[array][1])
    shifted_arrays = []
    for i, array in enumerate(translation_array):
        trans = translation_array[array]
        movement_x = trans[0]
        movement_y = trans[1]
        shifted_arrays.append(shift(arrays2shift[i], (movement_y, movement_x), cval=np.nan))

    return shifted_arrays


def centering_det(self, group='fluor', center_around=False, summed=False, default=False):
    """Return a detector that has been centered around a set value

    Parameters
    ==========
    self (SXDMFrameset)
        the sxdmframeset
    group (str)
        the group name the user would like to center to - acc_vals = fluor and roi
    center_around (bool)
        if this equals -1 then there will be no centering adjustments
    summed (bool)
        if True it will sum together all scans after centering
    default (bool)
        if True it will set the fluor image to center on or roi image to view to the first index

    Returns
    =======
    an array of the fluor images or the roi images for all the SXDMFrameset scans centered around
    the users value
    """
    if center_around == False:
        center_around = set_centering(self)
    else:
        pass
    array = return_det(file=self.file,
                       scan_numbers=self.scan_numbers,
                       group=group,
                       default=default)[0]

    if center_around != -1:
        ims = array_shift(self, array, center_around)
    else:
        ims = array
    if summed == False:
        return ims
    elif summed == True:
        return np.sum(ims, axis=0)


def set_centering(self):
    """Set the centering values for each scan

    Parameters
    ==========
    self (SXDMFrameset)
        the sxdmframeset

    Returns
    =======
    The centering index - sets all centering data
    """
    try:
        center_around = h5read_attr(file=self.file,
                                    loc=self.dataset_name + '/dxdy',
                                    attribute_name='centering')
        user_ask = input('A Centering Index of - ' + str(center_around) + ' - Has Been Found.' +
                         ' Would You Like To Use This Index To Center? y/n ')
        if user_ask == 'n':
            center_around = input('Which Scan Do You Want To Center Around? - Input Index - ')
            h5set_attr(file=self.file,
                       loc=self.dataset_name + '/dxdy',
                       attribute_name='centering',
                       attribute_val=center_around)

        elif user_ask == 'y':
            pass
        return int(center_around)

    except:
        center_around = input('Which Scan Do You Want To Center Around? - Input Index - ')
        h5set_attr(file=self.file,
                   loc=self.dataset_name + '/dxdy',
                   attribute_name='centering',
                   attribute_val=center_around)

    return int(center_around)


def ram_check():
    """Check how much RAM is being used.
    If it's over 90% then the analysis function stop loading information

    Returns
    =======
    the percent of RAM usage
    """
    mems = psutil.virtual_memory()
    return round(mems[2], 1)


def median_blur(input_array, median_blur_distance,
                cut_off_value_above_mean, with_low=False):
    """Median Blur a 1D array. Used for eliminating hot or dead pixels

    Parameters
    ==========
    input_array (1D array)
        a one dimensional numpy array
    median_blur_distance (int)
        the chunk size of numbers to to check for a median blur corrections
    cut_off_value_above_mean (int)
        the median_blur_height - amount above the mean to perform the median blur on

    Returns
    =======
    a 1 dimensional numpy array that has been median blurred
    """
    iteration_number = np.shape(input_array)[0]
    # Finds out the length of the array you want to median blur. This equals the number of iterations you will perform

    median_array = []
    for j in range(0, iteration_number):
        median_array = []
        # Corrects bounds if the program is out of bounds
        if j - median_blur_distance < 0:
            its_blur = range(0, j + median_blur_distance + 1)
        if j + median_blur_distance > iteration_number:
            its_blur = range(j - median_blur_distance, iteration_number)
        if j - median_blur_distance >= 0 and j + median_blur_distance <= iteration_number:
            its_blur = range(j - median_blur_distance, j + median_blur_distance + 1)
        # Takes the indicies for one iteration and gets the values of these locations from the users array
        for i in its_blur:
            try:
                median_array.append(input_array[i])
            except:
                pass
        # Replace a high value with the median value
        if input_array[j] > np.median(
                median_array) + cut_off_value_above_mean:
            input_array[j] = np.median(median_array)
        elif with_low == True and input_array[j]<np.median(median_array)-cut_off_value_above_mean:
            input_array[j] = np.median(median_array)
        else:
            pass

    return input_array


def grab_dxdy(self):
    """Return the dxdy movements for each scan

    Parameters
    ==========
    self (SXDMFrameset)
        the sxdmframeset

    Returns
    =======
    the dxdy values stored in the self.file
    """
    data = h5grab_data(file=self.file,
                       data_loc=self.dataset_name + '/dxdy')
    store = {}
    for i, d in enumerate(data):
        store[i] = (d[0], d[1])
    return store


def get_idx4roi(pix, destination, scan_numbers):
    """Based on the pixel being loaded, this returns the index of each scan used in the self.scan_numbers

    Parameters
    ==========
    pix (array of strings)
        the image numbers for each scan for a given pixel
    destination (array of strings)
        full diffraction image locations for each scan for a given pixel
    scan_numbers (array of strings)
        the self.scan_numbers value

    Returns
    =======
    an array of index values for a master roi used to store values in the correct position
    """
    scan_splitter_counter = 0
    scan_numbers_counter = 0
    working = True
    scan_splitter = [destin.split('/')[1] for destin in destination]
    idx_store = []
    #print(pix, 'pix')
    for value in pix:
        #print(value)
        if np.isnan(value) == False:
           # print('second val', value)
            idx_store.append(scan_numbers_counter
                             )
            #print(scan_splitter[scan_splitter_counter], scan_numbers[scan_numbers_counter])
            if scan_splitter[scan_splitter_counter] != scan_numbers[scan_numbers_counter]:
                #print(value, 'failure')
                working = False
            scan_splitter_counter = scan_splitter_counter + 1
            scan_numbers_counter = scan_numbers_counter + 1
        else:
            scan_numbers_counter = scan_numbers_counter + 1
        #print(scan_splitter_counter, scan_numbers_counter)

    if working == False:
        warnings.warn('Program ROI IDX Fail')
    return idx_store


def create_rois(self):
    """Take the self.roi_results and make them into something more useful

    Parameters
    ==========
    self (SXDMFrameset)
        the sxdmframset

    Returns
    =======
    the region of interst maps for each scan, the region of interest maps for the user defined
    sub regions of interest
    """
    # Create blank arrays
    scan_rois = np.empty((len(self.scan_numbers),
                          self.roi_analysis_total_rows,
                          self.roi_analysis_total_columns))
    try:
        sub_rois = np.empty((len(self.diff_segment_squares),
                             self.roi_analysis_total_rows,
                             self.roi_analysis_total_columns))
    except:
        print('self.diff_segment_squares is not defined. using default value')
        sub_rois = np.empty((1,
                             self.roi_analysis_total_rows,
                             self.roi_analysis_total_columns))

    # take the roi_results value and place them into a usable numpy array
    for pixel in self.roi_results:
        # Scan ROI
        row = pixel[0][0]
        column = pixel[0][1]
        scan_idxs = pixel[1].copy()
        scan_vals = pixel[4].copy()

        for i, idx in enumerate(scan_idxs):
            scan_rois[idx][row][column] = scan_vals[i]

        # User Sub Region
        sub_vals = pixel[7].copy()

        for j, val in enumerate(sub_vals):
            sub_rois[j][row][column] = val

    return scan_rois, sub_rois


def grab_fov_dimensions(self):
    """Returns the image dimensions for the User

    Parameters
    ==========
    self (SXDMFrameset)
        the sxdmframeset

    Returns
    =======
    the np.shape() of the fluorescence images - which are identical for the the entire field of view
    """
    image = return_det(self.file, self.scan_numbers, group='fluor', default=True)
    return np.shape(image[0])


def results_2dsum(self):
    """Returns the 2d summed diffraction pattern from the results self.saved_file without loading all the diffraction
    data

    Parameters
    ==========
    self (SXDMFrameset)
        the sxdmframeset object

    Returns
    =======
    2d image array of the summed diffraction pattern
    """

    counter = 0
    for i in range(0, self.roi_analysis_total_rows):
        for j in range(0, self.roi_analysis_total_columns):
            f = h5py.File(self.save_filename, 'r')
            spot_dif = f['{}/summed_dif'.format(self.dataset_name)][counter]
            counter = counter + 1
            try:
                store = np.add(store, spot_dif)
            except:
                store = spot_dif

            f.close()

    return store