import numpy as np
from astropy import units as u
from astropy import constants as const
import types

__imports = [val.__name__ for name, val in globals().items() if isinstance(val, types.ModuleType)]

print(f'Hello this is the standard cx python setup')
print(f'The following packages have been loaded: {__imports}')
