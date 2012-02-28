# test_fedexvalidation
"""
    Tests for Address Validation
    fog133
"""
import logging
logging.basicConfig(level=logging.INFO)
# if you want to see the suds messages... uncomment
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

from erp.lib.validate_address import AltaAddressValidationRequest
from fedex.config import FedexConfig

fedex_key = 'xSCiJwCcSd6qutOe'
fedex_password = 'a5QOIN10O05YTX4q5xacDGVqB'

params = {'street_lines':None,'city':None,'province':None,'postal_code':None}

params['street_lines'] = ['320 MLK Jr DR SE','APT9']
params['city'] = 'Atlanta'
params['province'] = 'GA'
params['postal_code'] = '30312'
params['country_code'] = 'US'

fedconf = FedexConfig(fedex_key, fedex_password)
request = AltaAddressValidationRequest(fedconf, **params)

request.send_request()
