import unittest
import pdb
from obs4MIPs_process import process
from Toolbox.ESGFresources import ESGFresources
from Toolbox import CMORresources

class  TestECMWF(unittest.TestCase):
   def setUP(self):
      pass
   def test_numbers_3_4(self):
      self.assertEqual( 3*4, 12)

   def test_ECMWF(self):
      # -----------------------
      # Read in "rc" file
      # -----------------------
      pdb.set_trace()
#      rc=ESGFresources.__init__( "ECMWF.rc" )
      rc=ESGFresources( "ECMWF.rc" )
      rc['outpath'] = "."
      oTable             = CMORresources.CMORTable( rc['inpath'], rc['table'] )
      rc['project_id']   = oTable[ 'project_id'     ]
      rc['product']      = oTable[ 'product'        ]
      rc['modeling_realm'] = oTable[ 'modeling_realm' ]
      rc['frequency']      = oTable[ 'frequency'      ]
      process(rc)



if __name__ == '__main__':
   unittest.main()


