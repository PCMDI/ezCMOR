#  Class factory
#
#  Select the right handler depending on the file format

import os
import pdb
import sys
import magic
import scipy.io
import cdtime
import numpy.ma as ma
import numpy
import netCDF4
import cdms2
import re

from cdms2.grid import createUniformGrid
from cdms2.grid import createGenericGrid
from cdms2      import createVariable

#  ********************************************************************
#     import_equation()
#
#  provide equation dynamically
#  ********************************************************************
def import_equation(eq):
    d = eq.rfind(".")
    EqName = eq[ d+1:len(eq) ]
    m = __import__( eq[0:d], globals( ), locals( ), [ EqName ] )
    return getattr( m, EqName )

#  ********************************************************************
#     HandlerGrads()
#
#  Manage Grads file io
#  ********************************************************************
class HandlerGrads(object):
    '''
    '''
    def __new__(klass, *args, **kwargs):
        # ------------------------------------------------------------------
        # This return make sure __init__ is begin called after the class is
        # created
        # ------------------------------------------------------------------
        return super(HandlerGrads, klass).__new__(klass, *args, **kwargs)

    def __init__(self):
        pass

    def open(self, file, variable=None):
        '''
        Open ctl file and read data
        '''
        #pdb.set_trace()
        self.f=cdms2.open(file)            
        self.variable=variable
        self.data=self.f(variable)     # read variable            

        
    def getData(self, variable=None):
        '''
        Return data array
        '''
        if( variable != None ):
            data=self.f(variable)
        else:
            data=self.data

        return data
    
    def getLongitude(self):
        '''
        Return Longitude.
        '''
        return self.data.getLongitude()
    
    def getLatitude(self):
        '''
        Return Latitude.
        '''
        return self.data.getLatitude()

    def getTime(self,timeunits=None):
        '''
        Return time in cdtime format.
        '''
        if(timeunits == 'internal'):
            timeunits=self.getTimeUnits()
        
        time_values = numpy.arange(len(self.data.getTime()))
        time_bounds = numpy.arange(len(self.data.getTime())+1)
        cur_time=[cdtime.reltime(i,timeunits) 
                  for i in time_values]
        
        return cur_time
    
    def getTimeUnits(self,timeunits):
        '''
        return Time units (month since yyyy)
        '''
        if( timeunits == 'internal' ):
            return self.data.getTime().units
        return timeunits
        

#  ********************************************************************
#     HandlerHDF4()
#
#  Manage HDF4 file io.  Note, this API reads HDF4 and Netcdf4/HDF5
#  ********************************************************************
class HandlerHDF4(object):
    '''
    '''
    def __new__(klass, *args, **kwargs):
        # ------------------------------------------------------------------
        # This return make sure __init__ is begin called after the class is
        # created
        # ------------------------------------------------------------------
        return super(HandlerHDF4, klass).__new__(klass, *args, **kwargs)

    def __init__(self):
        pass

    def open(self, file, variable=None):
        '''
        Open ctl file and read data
        '''
        #pdb.set_trace()
        self.f=netCDF4.Dataset(file,'r')            
        self.data=self.f.variables[variable][:].astype('float32')     # read variable            

        # --------------------------------------------------
        # Look for Coordinate variables keys
        # --------------------------------------------------
        TimeKey = [key  for key in self.f.variables.keys() \
                        if self.f.variables[key].ncattrs() != [] \
		        if "since"         in self.f.variables[key].units ][0]

        LonKey  = [key  for key in self.f.variables.keys() \
                        if self.f.variables[key].ncattrs() != [] \
                        if "degrees_east"  in self.f.variables[key].units ][0]

        LatKey  = [key  for key in self.f.variables.keys() \
                        if self.f.variables[key].ncattrs() != [] \
                        if "degrees_north" in self.f.variables[key].units ][0]

        LevKey  = [key  for key in self.f.variables.keys() \
                        if self.f.variables[key].ncattrs() != [] \
                        if "hPa"           in self.f.variables[key].units ]


        self.TimeKey = TimeKey
        nlat = self.f.variables[LatKey].shape[0]
        nlon = self.f.variables[LonKey].shape[0]
        lat  = self.f.variables[LatKey][:]
        lon  = self.f.variables[LonKey][:]

        
        # -------------------------------
        # Used cdms2 API to create grid
        # --------------------------------
        self.grid = createGenericGrid( lat,lon, order="yx" )
        fillValue = self.f.variables[variable]._FillValue
        data      = self.f.variables[variable][:]
        
        # -------------------------------
        # Create level axis
        # --------------------------------
        levAxis=[]
        if ( LevKey != [] ):
          #pdb.set_trace()
          levels=self.f.variables[LevKey[0]][:]
          levAxis = cdms2.createAxis(levels, bounds=None)
          levAxis.designateLevel(persistent=True)
          levAxis.units=self.f.variables[LevKey[0]].units
          levAxis.long_name=self.f.variables[LevKey[0]].long_name


        time=self.f.variables[TimeKey[:]]
        timeAxis = cdms2.createAxis(time, bounds=None)
        timeAxis.designateTime(persistent=True, calendar = cdtime.MixedCalendar)
        self.data = cdms2.createVariable(data, fill_value=fillValue, grid=self.grid)
        if ( LevKey != [] ): 
            self.data.setAxis(1,levAxis)
        self.data.setAxis(0,timeAxis)
        

        
    def getData(self,variable=None):
        '''
        Return data array
        '''
        if( variable != None ):
           data = None
           try:
              data = self.f.variables[variable][:].astype('float32')
              return data
           except:
              return None
        return self.data
    
    def getLongitude(self):
        '''
        Return Longitude.
        '''
        return self.data.getLongitude()
    
    def getLatitude(self):
        '''
        Return Latitude.
        '''
        return self.data.getLatitude()

    def getTime(self,timeunits=None):
        '''
        Return time.
        '''
        timeunits=self.getTimeUnits( timeunits )

        time_values =   self.f.variables[self.TimeKey][:]
 
        cur_time=[ cdtime.reltime( i, timeunits ) 
                   for i in time_values ]
        
        return cur_time
    def getTimeUnits(self,timeunits):
        '''
        return Time units (month since yyyy)
        '''
        if( timeunits == 'internal' ):
            return self.f.variables[self.TimeKey].units
        return timeunits


#  ********************************************************************
#     HandlerNetCDF()
#
#  Manage netCDF file io.  Note, this API reads HDF4 and Netcdf4/HDF5
#  ********************************************************************
class HandlerNetCDF(object):
    '''
    '''
    def __new__(klass, *args, **kwargs):
        # ------------------------------------------------------------------
        # This return make sure __init__ is begin called after the class is
        # created
        # ------------------------------------------------------------------
        return super(HandlerNetCDF, klass).__new__(klass, *args, **kwargs)

    def __init__(self):
        pass

    def open(self, file, variable=None):
        '''
        Open ctl file and read data
        '''
        self.f=cdms2.open(file)            
        self.data=self.f(variable).astype('float32')     # read variable            

        
    def getData(self, variable=None):
        '''
        Return data array
        '''
        if( variable != None ):
            data=self.f(variable)
        else:
            data=self.data
        return data
    
    def getLongitude(self):
        '''
        Return Longitude.
        '''
        return self.data.getLongitude()
    
    def getLatitude(self):
        '''
        Return Latitude.
        '''
        return self.data.getLatitude()

    def getTime(self,timeunits=None):
        '''
        Return time.
        '''
        if( timeunits == 'internal' ):
            timeunits=self.getTimeUnits()

        time_values =   self.f.getAxis("time")[:]
        #pdb.set_trace()
        time_bounds = time_values
        if( len(time_values) == 1 ):
            numpy.append(time_bounds, 1 )
        else:
            deltime = time_values[ 1 ] - time_values[ 0 ]
            numpy.append(time_bounds, time_values[-1] + deltime )

        cur_time=[ cdtime.reltime( i, timeunits ) 
                   for i in time_values ]
        
        return cur_time
    def getTimeUnits(self,timeunits):
        '''
        return Time units (month since yyyy)
        '''
        if( timeunits == 'internal' ):
            return self.data.getTime().units
        return timeunits


#  ********************************************************************
#     HandlerNCAggregate()
#
#  Aggreate a list of NetCDF files from a text file
#  Each file must have the same lat/lon dimension
#  ********************************************************************
class HandlerNCAggregate(object):
    '''
    '''
    def __new__(klass, *args, **kwargs):
        # ------------------------------------------------------------------
        # This return make sure __init__ is begin called after the class is
        # created
        # ------------------------------------------------------------------
        return super(HandlerNCAggregate, klass).__new__(klass, *args, **kwargs)

    def __init__(self):
        '''
        Nothing to do
        '''
        self.prefix = []

    def open(self, file, variable=None):
        '''
        Make sure that all files in the list exist
        '''
        f = open(file,'r')
        self.flist = f.readlines()
        f.close()
        
        for file in self.flist:
            filename=file.strip()
            if( not os.path.exists(filename) ):
                print "File %s does not exist in filelist" % filename

        # --------------------------------------------------------
        # Extract General information from first file in the list
        # ---------------------------------------------------------
        #pdb.set_trace()
        firstfile = cdms2.open(self.flist[0].strip(),'r')
        var=[v for v in firstfile.variables.keys() if (len(v) == len(variable)) and (v[v.find(variable):] == variable) ]
        prefix=[v[:(v.find(variable)-1)] for v in firstfile.variables.keys() if (len(v) == len(variable)) and (v[v.find(variable):] == variable)]

        self.variable = firstfile(var[0])
        self.missing_value = self.variable.missing_value
        self.prefix = prefix

        # ----------------------------
        # Read first file in the list
        # -----------------------------
        self.timeunits = self.variable.getTime().units

    def getData(self, variable=None):
        '''
        Aggreate all data from the file list in the order given.
        '''
        #pdb.set_trace()
        rel_time=[]
        filename = self.flist[0].strip()
        f = cdms2.open( filename, 'r' )

        if( variable != None ):
            self.vartoread = variable
            self.variable = f(variable)
            self.timeunits = self.variable.getTime().units
        else:
            self.vartoread = self.variable.id
            
        timeunits =   f(self.vartoread).getTime().units
        TimeValues = f(self.vartoread).getTime()[:]
        cur_time_values = [ cdtime.reltime(TimeValues[i], timeunits ) for i in range(len(TimeValues)) ]
        rel_time_values = [ cur_time_values[i].torel("days since 1900-01-01").value for i in range(len(TimeValues)) ]
        rel_time = rel_time + rel_time_values
        axisList = f(self.vartoread).getAxisList()
        data = f(self.vartoread)[:]
        print "reading %s" % filename.strip()
        if( self.prefix != [] ):
            data.prefix = self.prefix[0]

        # ---------------------------
        # Concatenate following files
        # ---------------------------
        for filename in self.flist[ 1: ]:
            print "reading %s" % filename.strip()
            f = cdms2.open( filename.strip(), 'r' )
            timeunits =   f(self.vartoread).getTime().units
            TimeValues = f(self.vartoread).getTime()[:]
            cur_time_values = [ cdtime.reltime(TimeValues[i], timeunits ) for i in range(len(TimeValues)) ]
            rel_time_values = [ cur_time_values[i].torel("days since 1900-01-01").value for i in range(len(TimeValues)) ]
            rel_time = rel_time + rel_time_values
            data2 = f(self.vartoread)[:]
            data = numpy.ma.concatenate((data,data2), axis=0)
            f.close()
        tupletime = tuple([i for i in rel_time])
        axisList[0]._data_=tupletime
        axisList[0].units="days since 1900-01-01"
        data.setAxisList(axisList)
        return data

    
    def getLongitude(self):
        '''
        Assume same grid for all files.
        '''
        return self.variable.getLongitude()
        
    
    def getLatitude(self):
        '''
        Assume same grid for all files.
        '''
        return self.variable.getLatitude()


    def getTime(self,timeunits=None):
        '''
        Return time.
        Assume that file time variable name will be the same in all files.
        '''
        flist=self.flist
        nbFiles = len(self.flist)
        # ----------------------------
        # Read first file in the list
        # -----------------------------
        time = self.variable.getTime()[:]

        # ---------------------------
        # Concatenate following files
        # ---------------------------
        for filename in self.flist[ 1: ]:
            f = cdms2.open( filename.strip(), 'r' )
            time2      =   f(self.variable.id).getTime()
            timeunits2 =   f(self.variable.id).getTime().units
            match=re.match('.*since.*', timeunits2)
            # ---------------------------------------------------
            # if timeunits is not UDUNITS format, pass back value 
            # and let InputTimeUnits attribute to take care of
            # the conversion.  
            # ----------------------------------------------------
            if( not match ):  timeunits2=self.timeunits
            # --------------------------------
            # Make sure we have the same units
            # ---------------------------------
            if( timeunits2 != self.timeunits ):
                file_time = [ cdtime.reltime(time2[ i ], timeunits2 ) \
                             for i in range( len( time2 ) )]
                time2 = [ file_time[i].torel( timeunits ).value       \
                          for i in range( len( time2 ) ) ]

            time2=time2[:]
            time = numpy.concatenate((time,time2), axis=0)
            f.close()

        self.time = [cdtime.reltime(i,self.timeunits) for i in time]
        return self.time

    
    def getTimeUnits(self,timeunits=None):
        '''
        return Timeunits.
        '''
        # ---------------------------------------------------
        # If file timeunits are UDUNITS compliante, overwrite
        # timeunits argument
        # ---------------------------------------------------
        match = re.match('.*since.*',self.variable.getTime().units)
        if( match ):
           return self.variable.getTime().units
        self.timeunits=timeunits
        return timeunits
        
    
#  ********************************************************************
#  MatlabData()
#
#  Manage Matlab data object.
#
#  Note: Assume that data is in the key that is not internal to Matlab.
#        Matlab internal keys are surrounded by underscores (__key__).
#  ********************************************************************
class MatlabData(object):
    '''
    Convert Matlab data Array to cmor2 data Array.
    Create lat/lon grid
    '''


    def __init__(self,oMatlab):
        '''
        Read data and flip y axis.
        Assume data is -180 to 180 and will be shifted to get an array from
            0 to 360 degrees.
        
        '''
        DataKey = [key for key in oMatlab.keys()
                   if key not in ['__version__', '__header__', '__globals__']]

        # ---------------------------------------
        # Read in Data as a Numpy masked array.
        # ---------------------------------------
        self.data=ma.array(data=oMatlab[DataKey[0]], \
                   fill_value=0.0, \
                   copy=0,         \
                   dtype='float32' )
        
        # ----------------------------------------------
        # Assume fill value is 0 (Need to pass a value)
        # -----------------------------------------------
        self.data=ma.masked_values(self.data,0)

        # -----------------------------------------------
        # Transpose 3D matrix to get the time axis first
        # -----------------------------------------------
        self.data=self.data.transpose(2,0,1)

        # -------------
        # Flip y axis
        # -------------
        self.data=self.data[:,::-1,:]

        # --------------------------------------------------
        # Extract X lenght and Y length to compute Lat/Lon
        # --------------------------------------------------
        nlat = self.data.shape[1]
        nlon = self.data.shape[2]

        # --------------------------------------------------------------------
        # shift array from -180 to 180 degrees to 0 to 360 degrees
        # The last half of the array becomes the first half and the first half
        # becomes the last half
        # --------------------------------------------------------------------
        flipped=ma.array( numpy.zeros( self.data.shape ), \
                 fill_value=0.0, \
                 dtype='float32' )

        # -----------------------------------------
        # Masked fill_value (default to 0 for now)
        # -----------------------------------------
        flipped=ma.masked_values(flipped,0)

        flipped[:,:,-nlon/2:]=self.data[:,:,:nlon/2]
        flipped[:,:,:nlon/2] =self.data[:,:,-nlon/2:]

        # ---------------------------------
        # New flipped array becomes the data.
        # ----------------------------------
        self.data=flipped
        flipped=0 # In order to save memory

        # -------------------------------------------------------
        # Compute latitudes longitude from X length and Y Length
        # Assume Global data on cylindrical rectangular grid.
        # -------------------------------------------------------
        deltaLat = 180.0/nlat
        deltaLon = 360.0/nlon
        startLat = -90  + (deltaLat/2.0)
        startLon = 0 + (deltaLon/2.0)
        
        # -------------------------------
        # Used cdms2 API to create grid
        # --------------------------------
        self.grid= createUniformGrid( startLat, nlat, deltaLat, \
                   startLon, nlon, deltaLon)
        
    def getData(self):
        '''
        return data array
        '''
        return self.data
    
    def getLatitude(self):
        '''
        return lattitude array
        '''
        return  self.grid.getLatitude()
    
    def getLongitude(self):
        '''
        return longitude array
        '''
        return self.grid.getLongitude()
    
    def getTime( self, cur_timeunits ):
        '''
        '''
        nTime = self.data.shape[0]
        time_values = numpy.arange(nTime)
        fileTime =[ cdtime.reltime(i, cur_timeunits)
                    for i in time_values ]
        
        return fileTime

    def getTimeUnits(self,timeunits):
        '''
        return Time units (month since yyyy)
        '''
        return timeunits


    def __getitem__(self, key):
        '''
        '''
        return self.getData()
    
#  ********************************************************************
#     HandlerMatlab()
#
#  Manage Matlab data file.
#
#  Note: Assume that data is in the key that is not internal to Matlab.
#  ********************************************************************
class HandlerMatlab(object):
    '''    
    '''
    def __new__(klass, *args, **kwargs):
        # ------------------------------------------------------------------
        # This return make sure __init__ is begin called after the class is
        # created
        # ------------------------------------------------------------------
        return super(HandlerMatlab, klass).__new__(klass, *args, **kwargs)

    def __init__(self):
        pass

    def open(self, file, variable=None):
        '''
        Open Matlab and read data
        '''
        self.f=scipy.io.loadmat(file)
        self.oMatlab=MatlabData(self.f)

        
    def getData(self):
        '''
        Return data array
        '''
        return self.oMatlab.getData()
    
    def getLongitude(self):
        '''
        Return Longitude.
        '''
        return self.oMatlab.getLongitude()
    
    def getLatitude(self):
        '''
        Return Latitude.
        '''
        return self.oMatlab.getLatitude()

    def getTime(self,timeunits):
        '''
        Return time.
        '''
        return self.oMatlab.getTime(timeunits)

    def getTimeUnits(self,timeunits):
        '''
        return Time units (month since yyyy)
        '''
        return self.oMatlab.getTimeUnits(timeunits)

    

#  ********************************************************************
#  HandlerFormats()
#
#  Factory detecting file format and return a pointer to the related
#  format class
#
#  Reference:
#     http://code.activestate.com/recipes/576687/
#
#  ********************************************************************
class HandlerFormats(object):
    '''
    Rerturn Format Hanlder depending on file magic number.
    '''
    Formats= {'NetCDF Data Format data': HandlerNetCDF,
              'Hierarchical Data Format (version 5) data': HandlerNetCDF,
              'Hierarchical Data Format (version 4) data': HandlerHDF4,
              'NCList': HandlerNCAggregate,
              'DSET'  : HandlerGrads,
              'Matlab': HandlerMatlab}

    def __new__( klass, filename ):
        #pdb.set_trace()
        MagicNumber = magic.from_file( filename )
        try:
            return HandlerFormats.Formats[MagicNumber]()
        except:
            try:
                return HandlerFormats.Formats[MagicNumber]()
            except:
                # --------------------------------------------------------------------------------
                # Magic is too relax and come backup with 'Bio-Rad .PIC Image File'
                # Since we will never read these files in the program, I just assume this will be 
                # a list of files.
                # --------------------------------------------------------------------------------
                if((MagicNumber[0:5] == 'ASCII') or  (MagicNumber[0:5] == "Bio-R")):
                    f=open(filename,'r')
                    lines=f.readlines()
                    for line in lines:
                        if(line[0:4].upper() == 'DSET'):
                            return HandlerFormats.Formats['DSET']()
                        elif( line.strip().find(".nc") or line.strip().endswith("hdf") ):
                            return HandlerFormats.Formats['NCList']()
                    
    def __init__(self, filename ):
        pass
    



