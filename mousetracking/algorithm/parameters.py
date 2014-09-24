'''
Created on Aug 27, 2014

@author: David Zwicker <dzwicker@seas.harvard.edu>

Provides a dictionary with default parameters for the mouse tracking.
This can also be seen as some kind of documentation of the available
parameters.
'''

from __future__ import division

import os
from collections import namedtuple


# enum of different units that we use
class UNIT(object):
    FACTOR = 1
    FRACTION = 2
    FOLDER = 3
    COLOR = 4
    LENGTH_PIXEL = 11
    AREA_PIXEL = 12
    TIME_FRAMES = 20
    RATE_FRAMES = 21
    SPEED_PIXEL_FRAME = 30
    

Parameter = namedtuple('Parameter', ['key', 'default_value', 'unit', 'description'])


PARAMETER_LIST = [
    # Video input
    Parameter('video/filename_pattern', 'raw_video/*.MTS', UNIT.FOLDER,
              'Filename pattern used to look for videos'),
    Parameter('video/initial_adaptation_frames', 100, UNIT.TIME_FRAMES,
              'Number of initial frames to skip during analysis'),
    Parameter('video/blur_radius', 3, UNIT.LENGTH_PIXEL,
              'Radius of the blur filter to remove noise'),
    Parameter('video/blur_sigma_color', 10, UNIT.COLOR,
              'Standard deviation in color space of the bilateral filter'),
    Parameter('video/frames', None, None,
              'Frames of the video which are analyzed [start and end index should be given]'),
    Parameter('video/cropping_rect', None, None,
              "Rectangle to which the video is cropped. This can be either four "
              "numbers [left, top, width, height] or some string like "
              "'upper left', 'lower right', etc."),
          
    # Logging
    Parameter('logging/enabled',  True, None,
              'Flag indicating whether logging is enabled'),
    Parameter('logging/folder', './logging/', UNIT.FOLDER,
              'Folder to which the log file is written'),
    Parameter('logging/level_stderr', 'WARN', None,
              'Level of messages to log to stderr [standard python logging levels]'),
    Parameter('logging/level_file', 'INFO', None,
              'Level of messages to log to file if folder is set '
              '[standard python logging levels]'),
            
    # Debug
    Parameter('debug/output', [], None,
              'List of identifiers determining what debug output is produced'),
    Parameter('debug/folder', './debug/', UNIT.FOLDER,
              'Folder to which debug videos are written'), 
    Parameter('debug/output_period', 100, UNIT.TIME_FRAMES,
              'How often are frames written to the output file'),
    Parameter('debug/window_position', None, None,
              'Position (x, y) of the top-left corner of the debug window'),
            
    # Output
    Parameter('output/folder', './results/', UNIT.FOLDER,
              'Folder to which the YAML and HDF5 result files are written'),
    Parameter('output/video/folder', './results/', UNIT.FOLDER,
              'Folder to which the result video is written'),
    Parameter('output/output_period', 1, UNIT.TIME_FRAMES,
              'How often are frames written to the output file or shown on the '
              'screen'),
    Parameter('output/video/extension', '.mov', None,
              'File extension used for debug videos'),
    Parameter('output/video/codec', 'libx264', None,
              'ffmpeg video codec used for debug videos'),
    Parameter('output/video/bitrate', '2000k', None,
              'Bitrate used for debug videos'),
    
    # Cage
    Parameter('cage/determine_boundaries', True, None,
              'Flag indicating whether the cropping rectangle should be determined '
              'automatically. If False, we assume that the original video is '
              'already cropped'),
    Parameter('cage/width_min', 650, UNIT.LENGTH_PIXEL,
              'Minimal width of the cage. This is only used to make a '
              'plausibility test of the results'),
    Parameter('cage/width_max', 800, UNIT.LENGTH_PIXEL,
              'Maximal width of the cage. This is only used to make a '
              'plausibility test of the results'),
    Parameter('cage/height_min', 400, UNIT.LENGTH_PIXEL,
              'Minimal height of the cage. This is only used to make a '
              'plausibility test of the results'),
    Parameter('cage/height_max', 500, UNIT.LENGTH_PIXEL,
              'Maximal height of the cage. This is only used to make a '
              'plausibility test of the results'),
    Parameter('cage/linescan_width', 30, UNIT.LENGTH_PIXEL,
              'Width of the line scan use to detect the cage frame'),
    Parameter('cage/linescan_smooth', 5, UNIT.LENGTH_PIXEL,
              'Standard deviation used for smoothing the line scan profile'),
                
    # Colors               
    Parameter('colors/adaptation_interval', 1000, UNIT.TIME_FRAMES,
              'How often are the color estimates adapted'),
    Parameter('colors/std_min', 5, UNIT.COLOR,
              'Minimal standard deviation of sky and sand colors'),

    # Background and explored area                             
    Parameter('background/adaptation_rate', 1e-2, UNIT.RATE_FRAMES,
              'Rate at which the background is adapted'),
    Parameter('explored_area/adaptation_rate_outside', 1e-3, UNIT.RATE_FRAMES,
              'Rate at which the explored area is adapted outside of burrows'),
    Parameter('explored_area/adaptation_rate_burrows', 1e-5, UNIT.RATE_FRAMES,
              'Rate at which the explored area is adapted inside burrows'),
    
    # Ground
    Parameter('ground/point_spacing', 20, UNIT.LENGTH_PIXEL,
              'Spacing of the support points describing the ground profile'),
    Parameter('ground/linescan_length', 100, UNIT.LENGTH_PIXEL,
              'Length of the line scan used to determine the ground profile'),
    Parameter('ground/slope_detector_max_factor', 0.4, UNIT.FACTOR,
              'Factor important in the ridge detection step, where the ridge '
              'is roughly located by looking at vertical line scans and points '
              'with large slopes are located. The smaller this factor, the more '
              'such points are detected and the further up the profile is '
              'estimated to be'),
    Parameter('ground/curvature_energy_factor', 1, UNIT.FACTOR,
              'Relative strength of the curvature energy to the image energy '
              'in the snake model of the ground line'),
    Parameter('ground/snake_energy_max', 5, UNIT.FACTOR,
              'Determines the maximal energy the snake is allowed to have'),
    Parameter('ground/slope_max', 3, UNIT.FRACTION,
              'Maximal slope of the side ridges'),
    Parameter('ground/frame_margin', 50, UNIT.LENGTH_PIXEL,
              'Width of the margin to the frame in which the ground profile is '
              'not determined'),
    Parameter('ground/grabcut_uncertainty_margin', 100, UNIT.LENGTH_PIXEL,
              'Width of the region around the estimated profile, in which '
              'the GrabCut algorithm may optimize'),
    Parameter('ground/adaptation_interval', 100, UNIT.TIME_FRAMES,
              'How often is the ground profile adapted'),
    Parameter('ground/ridge_width', 5, UNIT.LENGTH_PIXEL,
              'Width of the ground profile ridge'),
    Parameter('ground/smoothing_sigma', 300, UNIT.TIME_FRAMES,
              'Standard deviation for Gaussian smoothing over time'),
    
    # Mouse and the associated tracking
    Parameter('mouse/intensity_threshold', 1, UNIT.FACTOR,
              'Determines how much brighter than the background (usually the '
              'sky) the mouse has to be. This value is measured in terms of '
              'standard deviations of the sky color'),
    Parameter('mouse/model_radius', 25, UNIT.LENGTH_PIXEL,
              'Radius of the mouse model'),
    Parameter('mouse/area_min', 100, UNIT.AREA_PIXEL,
              'Minimal area of a feature to be considered in tracking'),
    Parameter('mouse/area_mean', 700, UNIT.AREA_PIXEL,
              'Mean area of a mouse, which is used to score the mouse'),
    Parameter('mouse/speed_max', 30, UNIT.SPEED_PIXEL_FRAME,
              'Maximal speed of the mouse'),
    Parameter('mouse/max_rel_area_change', 0.5, UNIT.FACTOR,
              'Maximal area change allowed between consecutive frames'),
                  
    Parameter('tracking/weight', 0.5, UNIT.FACTOR,
              'Relative weight of distance vs. size of objects for matching them'),
    Parameter('tracking/moving_window', 20, UNIT.TIME_FRAMES,
              'Number of consecutive frames used for motion detection'),
    Parameter('tracking/moving_threshold', 15, UNIT.SPEED_PIXEL_FRAME,
              'Threshold speed above which an object is said to be moving'),
    Parameter('tracking/object_count_max', 7, None,
              'Maximal number of objects allowed in a single frame. If there are '
              'more objects, the entire frame is discarded'),
    Parameter('tracking/time_scale', 10, UNIT.TIME_FRAMES,
              'Time duration of not seeing the mouse after which we do not ' 
              'know where it is anymore'),
    Parameter('tracking/tolerated_overlap', 10, UNIT.TIME_FRAMES,
              'How much are two consecutive tracks allowed to overlap'),
    Parameter('tracking/initial_score_threshold', 1000, UNIT.FACTOR,
              'Initial threshold for building the tracking graph'),
    Parameter('tracking/end_node_interval', 1000, UNIT.TIME_FRAMES,
              'What time duration do we consider for start and end nodes'),
    Parameter('tracking/splitting_duration_min', 10, UNIT.TIME_FRAMES,
              'Track duration above which two overlapping tracks are split'),
        
    # Burrows
    Parameter('burrows/adaptation_interval', 100, UNIT.TIME_FRAMES,
              'How often are the burrow shapes adapted'),
    Parameter('burrows/cage_margin', 30, UNIT.LENGTH_PIXEL,
              'Margin of a potential burrow to the cage boundary'),
    Parameter('burrows/width', 20, UNIT.LENGTH_PIXEL,
              'Typical width of a burrow'),
    Parameter('burrows/width_min', 10, UNIT.LENGTH_PIXEL,
              'Minimal width of a burrow'),
    Parameter('burrows/area_min', 1000, UNIT.AREA_PIXEL,
              'Minimal area a burrow cross section has to have'),
    Parameter('burrows/ground_point_distance', 10, UNIT.LENGTH_PIXEL,
              'Maximal distance of ground profile to outline points that are '
              'considered exit points'),
    Parameter('burrows/centerline_segment_length', 25, UNIT.LENGTH_PIXEL,
              'Length of a segment of the center line of a burrow'),
    Parameter('burrows/curvature_radius_max', 50, UNIT.LENGTH_PIXEL,
              'Maximal radius of curvature the centerline is allowed to have'),
    Parameter('burrows/fitting_length_threshold', 100, UNIT.LENGTH_PIXEL,
              'Length above which burrows are refined by fitting'),
    Parameter('burrows/fitting_width_threshold', 30, UNIT.LENGTH_PIXEL,
              'Width below which burrows are refined by fitting'),
    Parameter('burrows/fitting_edge_width', 3, UNIT.LENGTH_PIXEL,
              'Width of the burrow edge used in the template for fitting'),
    Parameter('burrows/fitting_edge_R2min', -10, UNIT.FACTOR,
              'Minimal value of the Coefficient of Determination (R^2) above '
              'which the fit of a burrow edge is considered good enough and '
              'will be used'),
    Parameter('burrows/outline_simplification_threshold', 0.005, UNIT.FACTOR,
              'Determines how much the burrow outline might be simplified. '
              'The quantity determines by what fraction the total outline '
              'length is allowed to change'),
    Parameter('burrows/simplification_threshold_area', 10, UNIT.AREA_PIXEL,
              'Burrow outline points are removed when the resulting effective '
              'change is below this threshold'),
                  
    Parameter('factor_length', 1, UNIT.FACTOR,
              'A factor by which all length scales will be scaled'),
                  
    # Computation resources
    Parameter('resources/notification_email', 'dzwicker@seas.harvard.edu', None,
              'Email address of the user to be notified in case of problems.'),
    Parameter('resources/slurm_partition', 'general', None,
              'Name of the slurm partition to use for submitting jobs'),              
    Parameter('resources/pass1/cores', 4, None, 'Number of cores for pass 1'),
    Parameter('resources/pass1/time', 20*60, None, 'Maximal computation minutes for pass 1'),
    Parameter('resources/pass1/memory', 1000, None, 'Maximal RAM for pass 1 [in MB]'),
    Parameter('resources/pass2/cores', 2, None, 'Number of cores for pass 2'),
    Parameter('resources/pass2/time', 20*60, None, 'Maximal computation minutes for pass 2'),
    Parameter('resources/pass2/memory', 10000, None, 'Maximal RAM for pass 2 [in MB]'),
]

PARAMETERS = {p.key: p for p in PARAMETER_LIST}
PARAMETERS_DEFAULT = {p.key: p.default_value for p in PARAMETER_LIST}



def set_base_folder(parameters, folder, include_default=False):
    """ changes the base folder of all folders given in the parameter
    dictionary.
    include_default is a flag indicating whether the default parameters
    should also be included and their folders should be changed. """
    # convert to plain dictionary if it is anything else
    parameters_type = type(parameters)
    if parameters_type != dict:
        parameters = parameters.to_dict(flatten=True)
        
    if include_default:
        p_copy = PARAMETERS_DEFAULT.copy()
        p_copy.update(parameters)
        parameters = p_copy
        
    # adjust the folders
    for key, value in parameters.iteritems():
        if PARAMETERS[key].unit == UNIT.FOLDER:
            parameters[key] = os.path.join(folder, value)
            
    # return the result as the original type 
    return parameters_type(parameters)



def scale_parameters(parameters, factor_length=1, factor_time=1):
    """ takes a dictionary of parameters and scales them according to their
    unit and the given scale factors """
    # convert to plain dictionary if it is anything else
    parameters_type = type(parameters)
    if parameters_type != dict:
        parameters = parameters.to_dict(flatten=True)
        
    # scale each parameter in the list
    for key in parameters:
        unit = PARAMETERS[key].unit
        if unit == UNIT.LENGTH_PIXEL:
            parameters[key] *= factor_length
        elif unit == UNIT.AREA_PIXEL:
            parameters[key] *= factor_length**2
        elif unit == UNIT.TIME_FRAMES:
            parameters[key] *= factor_time
        elif unit == UNIT.RATE_FRAMES:
            parameters[key] /= factor_time
        elif unit == UNIT.SPEED_PIXEL_FRAME:
            parameters[key] *= factor_length/factor_time
            
    # return the result as the original type 
    return parameters_type(parameters)

