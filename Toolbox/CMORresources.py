#import netCDF4
import cdms2
import re
import pdb

#  ********************************************************************
#         CMORTable()
#
#  ********************************************************************
class CMORTable:   
    '''
    Create dictionary based on a file using key:value standard      
    '''
    def __init__( self, inpath, table, entry=None ):
        '''
        Read CMIP5 Table and convert into a dictionary
        '''
        #pdb.set_trace()
        f=open( inpath + '/' + table, 'r')

        if( f == None ):
            print "Table file %s does  not exist " % (inpath + "/" + table )

        lines = f.readlines()

        startParse=[0]
        stopParse=[len(lines)]

        # --------------------------------
        # extract user specified entry
        # -------------------------------
        if( entry != None ):
            startParse = [ i for i in range(len(lines)) \
                           if re.match( ".*entry.*"+entry+".*", lines[i] ) != None  ]
            stopParse  = [ i for i in range(startParse[0]+2, len(lines)) \
                         if re.match( ".*==========.*", lines[i] ) != None  ]
            
        self.dico = dict([ tuple(lines[i].split(":")) 
                           for i in range(startParse[0], stopParse[0])
                           if len(lines[i].split(':')) == 2 ] )

        # --------------------------------
        # extract levels
        # -------------------------------
        if 'requested' in self.dico.keys():

            self.dico['levels'] = self.dico['requested'].split('!')[0].split()
            # --------------
            # Convert to int
            # ---------------
            self.dico['levels'] = [ int( float( self.dico['levels'][i] ) )
                                    for i in range( len( self.dico['levels'] ) )]
            self.dico['levels'].sort()

    def __getitem__( self, key ):
        '''
        Get rid of end of line comments and strip new lines CR "/n"
        '''
        return self.dico[key].split("!")[0].strip()

    def __setitem__( self,key,value ):
        '''
        '''
        self.dico[key]=value

    def __delete__( self, key ):
        '''
        '''
        del self.dico[key]



#  ********************************************************************
#     Global Attributes
#
#  Manage Global Attributes in a cmor file
#  ********************************************************************
class CMORAttributes:
    '''
    Manage Global Attributes.
    '''
    def __init__( self, file ):
        '''
        Open Cmor file
        '''
        self.filename = file
        self.f = cdms2.open( self.filename, 'r+' )
        
    def GlbDel( self, attribute ):
        '''
        Delete attribute
        '''
        delattr(self.f,attribute)
        
    def GlbSet( self, attribute, value):
        '''
        Set attribute
        '''
        setattr(self.f,attribute,value)

    def close(self):
        '''
        '''
        self.f.close()

