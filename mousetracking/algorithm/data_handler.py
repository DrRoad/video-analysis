'''
Created on Aug 16, 2014

@author: zwicker

contains classes that manage data input and output 
'''

from __future__ import division

import collections
import datetime
import logging
import os
import sys

import numpy as np
import yaml

from .parameters import PARAMETERS_DEFAULT
import objects
from .objects.utils import LazyHDFValue, prepare_data_for_yaml
from video.io import VideoFileStack
from video.filters import FilterCrop, FilterMonochrome
from video.utils import ensure_directory_exists

import debug  # @UnusedImport


# dictionary of data items that are stored in a separated HDF file
# and will be loaded only on access
HDF_VALUES = {'pass1/ground/profile': objects.GroundProfileList,
              'pass1/objects/tracks': objects.ObjectTrackList,
              'pass1/burrows/tracks': objects.BurrowTrackList,
              'pass2/ground_profile': objects.GroundProfileTrack,
              'pass2/mouse_trajectory': objects.MouseTrack}

LOGGING_FILE_MODES = {'create': 'w', #< create new log file 
                      'append': 'a'} #< append to old log file


class LazyLoadError(RuntimeError): pass


class DataHandler(object):
    """ class that handles the data and parameters of mouse tracking """
    logging_mode = 'append'    

    def __init__(self, name='', parameters=None, read_data=False):
        self.name = name

        # initialize the data handled by this class
        self.video = None
        self.data = DataDict()
        self.data.create_child('parameters')
        self.data['parameters'].from_dict(PARAMETERS_DEFAULT)
        self.user_parameters = parameters

        self.initialize_parameters(parameters)
        self.data['analysis-state'] = 'Initialized parameters'

        if read_data:
            self.read_data()
        

    def initialize_parameters(self, parameters=None):
        """ initialize parameters """
        if parameters is not None:
            self.data['parameters'].from_dict(parameters)
            
        # create logger for this object
        self.logger = logging.getLogger(self.name)
        self.logger.handlers = []     #< reset list of handlers
        self.logger.propagate = False #< disable default logger 
        self.logger.setLevel(logging.DEBUG)
        
        # add default logger to stderr
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(levelname)7s: %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        level = logging.getLevelName(self.data['parameters/logging/level_stderr'])
        handler.setLevel(level)
        self.logger.addHandler(handler) 
        
        if self.data.get('parameters/logging/folder', None) is not None:
            # setup handler to log to file
            logfile = self.get_filename('log.log', self.data['parameters/logging/folder'])
            handler = logging.FileHandler(logfile, mode=LOGGING_FILE_MODES[self.logging_mode])
            handler.setFormatter(formatter)
            level = logging.getLevelName(self.data['parameters/logging/level_file'])
            handler.setLevel(level)
            self.logger.addHandler(handler) 
            
        # setup mouse parameters as class variables
        # => the code is not thread-safe if different values for these parameters are used in the same process
        # number of consecutive frames used for motion detection [in frames]
        moving_window = self.data.get('parameters/tracking/moving_window', None)
        if moving_window:
            objects.ObjectTrack.moving_window = moving_window
        moving_threshold = self.data.get('parameters/tracking/moving_threshold', None)
        if moving_threshold:
            threshold = objects.ObjectTrack.moving_window*moving_threshold
            objects.ObjectTrack.moving_threshold = threshold
        
        curvature_radius_max = self.data.get('parameters/burrows/curvature_radius_max', None)
        if curvature_radius_max:
            objects.Burrow.curvature_radius_max = curvature_radius_max 
        centerline_segment_length = self.data.get('parameters/burrows/centerline_segment_length', None)
        if centerline_segment_length:
            objects.Burrow.centerline_segment_length = centerline_segment_length
        ground_point_distance = self.data.get('parameters/burrows/ground_point_distance', None)
        if ground_point_distance:
            objects.Burrow.ground_point_distance = ground_point_distance
            

    def get_folder(self, folder):
        """ makes sure that a folder exists and returns its path """
        if folder == 'results':
            folder = os.path.abspath(self.data['parameters/output/result_folder'])
        elif folder == 'debug':
            folder = os.path.abspath(self.data['parameters/output/video/folder_debug'])
            
        ensure_directory_exists(folder)
        return folder


    def get_filename(self, filename, folder=None):
        """ returns a filename, optionally with a folder prepended """
        if self.name: 
            filename = self.name + '_' + filename
        else:
            filename = filename
        
        # check the folder
        if folder is None:
            return filename
        else:
            return os.path.join(self.get_folder(folder), filename)
      

    def log_event(self, description):
        """ stores and/or outputs the time and date of the event given by name """
        self.logger.info(description)
        
        # save the event in the result structure
        if 'event_log' not in self.data:
            self.data['event_log'] = []
        event = str(datetime.datetime.now()) + ': ' + description 
        self.data['event_log'].append(event)

    
    def load_video(self, video=None, crop_video=True):
        """ loads the video and applies a monochrome and cropping filter """
        # initialize the video
        if video is None:
            video_filename_pattern = os.path.join(self.data['parameters/video/filename_pattern'])
            self.video = VideoFileStack(video_filename_pattern)
        else:
            self.video = video

        # save some data about the video
        self.data.create_child('video/raw', {'frame_count': self.video.frame_count,
                                             'size': '%d x %d' % self.video.size,
                                             'fps': self.video.fps})
        try:
            self.data['video/raw/filecount'] = self.video.filecount
        except AttributeError:
            self.data['video/raw/filecount'] = 1

        # restrict the analysis to an interval of frames
        frames = self.data.get('parameters/video/frames', None)
        if frames is not None:
            self.video = self.video[frames[0]:frames[1]]
        else:
            frames = (0, self.video.frame_count)

        cropping_rect = self.data.get('parameters/video/cropping_rect', None)

        if crop_video and cropping_rect is not None:
            # restrict video to green channel if it is a color video
            color_channel = 'green' if self.video.is_color else None
            
            if isinstance(cropping_rect, str):
                # crop according to the supplied string
                self.video = FilterCrop(self.video, region=cropping_rect,
                                        color_channel=color_channel)
            else:
                # crop to the given rect
                self.video = FilterCrop(self.video, rect=cropping_rect,
                                        color_channel=color_channel)
                
        else: # user_crop is not None                
            # use the full video
            if self.video.is_color:
                # restrict video to green channel if it is a color video
                self.video = FilterMonochrome(self.video, 'green')
            else:
                self.video = self.video

            
    def write_data(self):
        """ writes the results to a file """

        self.log_event('Started writing out all data.')

        # prepare writing the data
        main_result = self.data.copy()
        
        # write large amounts of data to accompanying hdf file
        hdf_filename= self.get_filename('results.hdf5', 'results')
        for key, cls in HDF_VALUES.iteritems():
            if key in main_result:
                value = main_result.get_item(key, load_data=False)
                if not isinstance(value, LazyHDFValue):
                    assert cls == value.__class__
                    storage_manager = cls.storage_class.create_from_data(key, value, hdf_filename)
                    main_result[key] = storage_manager#.yaml_string
        
        # write the main result file to YAML
        filename = self.get_filename('results.yaml', 'results')
        with open(filename, 'w') as outfile:
            yaml.dump(prepare_data_for_yaml(main_result),
                      outfile,
                      default_flow_style=False,
                      indent=4)       
       
                        
    def read_data(self):
        """ read the data from result files.
        If load_from_hdf is False, the data from the HDF file is not loaded.
        """
        
        # read the main result file and copy data into internal dictionary
        filename = self.get_filename('results.yaml', 'results')
        self.logger.info('Read YAML data from %s', filename)
        
        with open(filename, 'r') as infile:
            self.data.from_dict(yaml.load(infile))
        
        # initialize the parameters read from the YAML file
        self.initialize_parameters(self.user_parameters)
        
        # initialize the loaders for values stored elsewhere
        hdf_folder = self.get_folder('results')
        for key, data_cls in HDF_VALUES.iteritems():
            if key in self.data:
                value = self.data.get_item(key, load_data=False) 
                storage_cls = data_cls.storage_class
                if isinstance(value, LazyHDFValue):
                    value.set_hdf_folder(hdf_folder)
                else:
                    lazy_loader = storage_cls.create_from_yaml_string(self.data[key],
                                                                      data_cls,
                                                                      hdf_folder)
                    self.data[key] = lazy_loader
        
        self.log_event('Read previously calculated data from files.')

 
    #===========================================================================
    # DATA ANALYSIS
    #===========================================================================
        
    def mouse_underground(self, position):
        """ checks whether the mouse is under ground """
        ground_y = np.interp(position[0], self.ground[:, 0], self.ground[:, 1])
        return position[1] - self.params['mouse.model_radius']/2 > ground_y



class DataDict(collections.MutableMapping):
    """ special dictionary class representing nested dictionaries.
    This class allows easy access to nested properties using a single key:
    
    d = DataDict({'a': {'b': 1}})
    
    d['a/b']
    >>>> 1
    
    d['c/d'] = 2
    
    d
    >>>> {'a': {'b': 1}, 'c': {'d': 2}}
    """
    
    sep = '/'
    
    def __init__(self, data=None):
        # set data
        self.data = {}
        if data is not None:
            self.from_dict(data)


    def get_item(self, key, load_data=True):
        try:
            if self.sep in key:
                # sub-data is accessed
                child, grandchildren = key.split(self.sep, 1)
                value = self.data[child].get_item(grandchildren, load_data)
            else:
                value = self.data[key] 
        except KeyError:
            raise KeyError(key)

        # load lazy values
        if load_data and isinstance(value, LazyHDFValue):
            try:
                value = value.load()
            except KeyError:
                # we have to relabel KeyErrors, since they otherwise shadow
                # KeyErrors raised by the item actually not being in the DataDict
                # This then allows us to distinguish between items not found in
                # DataDict (raising KeyError) and items not being able to load
                # (raising LazyLoadError)
                raise LazyLoadError, 'Cannot load item `%s`' % key, sys.exc_info()[2] 
            self.data[key] = value
            
        return value

    
    def __getitem__(self, key):
        return self.get_item(key)
        
        
    def __setitem__(self, key, value):
        if self.sep in key:
            # sub-data is written
            child, grandchildren = key.split(self.sep, 1)
            try:
                self.data[child][grandchildren] = value
            except KeyError:
                # create new child if it does not exists
                child_node = DataDict()
                child_node[grandchildren] = value
                self.data[child] = child_node
                
        else:
            self.data[key] = value
    
    
    def __delitem__(self, key):
        try:
            if self.sep in key:
                # sub-data is deleted
                child, grandchildren = key.split(self.sep, 1)
                del self.data[child][grandchildren]
    
            else:
                del self.data[key]
        except KeyError:
            raise KeyError(key)


    def __contains__(self, key):
        if self.sep in key:
            child, grandchildren = key.split(self.sep, 1)
            return child in self.data and grandchildren in self.data[child]

        else:
            return key in self.data


    # Miscellaneous dictionary methods are just mapped to data
    def __len__(self): return len(self.data)
    def __iter__(self): return self.data.__iter__()
    def keys(self): return self.data.keys()
    def values(self): return self.data.values()
    def items(self): return self.data.items()
    def iterkeys(self): return self.data.iterkeys()
    def itervalues(self): return self.data.itervalues()
    def iteritems(self): return self.data.iteritems()
    def clear(self): self.data.clear()
           
            
    def __repr__(self):
        return 'DataDict(' + repr(self.data) + ')'


    def create_child(self, key, values=None):
        """ creates a child dictionary and fills it with values """
        self[key] = self.__class__(values)
        return self[key]


    def copy(self):
        """ makes a shallow copy of the data """
        res = DataDict()
        for key, value in self.iteritems():
            if isinstance(value, (dict, DataDict)):
                value = value.copy()
            res[key] = value
        return res


    def from_dict(self, data):
        """ fill the object with data from a dictionary """
        if data is not None:
            for key, value in data.iteritems():
                if isinstance(value, dict):
                    if key in self and isinstance(self[key], DataDict):
                        # extend existing DataDict structure
                        self[key].from_dict(value)
                    else:
                        # create new DataDict structure
                        self[key] = DataDict(value)
                else:
                    # store simple value
                    self[key] = value

            
    def to_dict(self):
        """ convert object to a nested dictionary structure """
        res = {}
        for key, value in self.iteritems():
            if isinstance(value, DataDict):
                value = value.to_dict()
            res[key] = value
        return res

    
    def pprint(self, *args, **kwargs):
        """ pretty print the current structure as nested dictionaries """
        from pprint import pprint
        pprint(self.to_dict(), *args, **kwargs)

        
        