## @ingroup Analyses-Aerodynamics
# Supersonic_Zero.py
# 
# Created:            T. MacDonald
# Modified: Nov 2016, T. MacDonald
#           Apr 2019, T. MacDonald
#           Apr 2020, M. Clarke

# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------

import SUAVE
from SUAVE.Core import Data
from .Markup import Markup
from SUAVE.Analyses import Process

from .Vortex_Lattice import Vortex_Lattice
from .Process_Geometry import Process_Geometry
from SUAVE.Methods.Aerodynamics import Supersonic_Zero as Methods
from SUAVE.Methods.Aerodynamics.Common import Fidelity_Zero as Common
import numpy as np

# ----------------------------------------------------------------------
#  Class
# ----------------------------------------------------------------------
## @ingroup Analyses-Aerodynamics
class Supersonic_Zero(Markup):
    """This is an analysis based on low-fidelity models.

    Assumptions:
    None

    Source:
    Primarily based on adg.stanford.edu, see methods for details
    """ 
    def __defaults__(self):
        """This sets the default values and methods for the analysis.

        Assumptions:
        None

        Source:
        Concorde data used for determining defaults can be found in "Supersonic drag reduction technology in the 
        scaled supersonic experimental airplane project by JAXA" by Kenji Yoshida
        https://www.sciencedirect.com/science/article/pii/S0376042109000177

        Inputs:
        None

        Outputs:
        None

        Properties Used:
        N/A
        """         
        self.tag = 'Fidelity_Zero_Supersonic'
        
        # correction factors
        settings =  self.settings
        settings.fuselage_lift_correction           = 1.14
        settings.trim_drag_correction_factor        = 1.02
        settings.wing_parasite_drag_form_factor     = 1.1
        settings.fuselage_parasite_drag_form_factor = 2.3
        settings.viscous_lift_dependent_drag_factor = 0.38
        settings.drag_coefficient_increment         = 0.0000
        settings.spoiler_drag_increment             = 0.00 
        settings.oswald_efficiency_factor           = None
        settings.span_efficiency                    = None
        settings.maximum_lift_coefficient           = np.inf 
        settings.begin_drag_rise_mach_number        = 0.95
        settings.end_drag_rise_mach_number          = 1.2
        settings.transonic_drag_multiplier          = 1.25 
        settings.number_panels_spanwise             = None 
        settings.number_panels_chordwise            = None 
        settings.use_surrogate                      = True 
        settings.include_slipstream_effect          = False 
        settings.plot_vortex_distribution           = False
        
        # this multiplier is used to determine the volume wave drag at the peak Mach number
        # by multiplying the volume wave drag at the end drag rise Mach number
        settings.peak_mach_number                      = 1.04
        settings.cross_sectional_area_calculation_type = 'Fixed'
        # 'Fixed' means that the area is not able to vary with Mach number, so the number at the desired cruise condition should
        # be used
        # 'OpenVSP' is a desired future possibility. This would allow the cross sectional area to vary with Mach number, but is 
        # much more computationally intensive.        
        settings.volume_wave_drag_scaling    = 3.7 # 1.8-2.2 are given as typical for an SST, but 3.7 was found to be more accurate 
        # This may be due to added propulsion effects
        settings.fuselage_parasite_drag_begin_blend_mach = 0.91
        settings.fuselage_parasite_drag_end_blend_mach   = 0.99
        
        # vortex lattice configurations
        settings.number_panels_spanwise = 5
        settings.number_panels_chordwise = 1
        
        
        # build the evaluation process
        compute = self.process.compute
        
        compute.lift = Process()
        compute.lift.inviscid_wings                = Vortex_Lattice()
        compute.lift.vortex                        = Methods.Lift.vortex_lift  # SZ
        compute.lift.fuselage                      = Common.Lift.fuselage_correction
        compute.lift.total                         = Common.Lift.aircraft_total
        
        compute.drag = Process()
        compute.drag.compressibility               = Process()
        compute.drag.compressibility.total         = Methods.Drag.compressibility_drag_total # SZ        
        compute.drag.parasite                      = Process()
        compute.drag.parasite.wings                = Process_Geometry('wings')
        compute.drag.parasite.wings.wing           = Common.Drag.parasite_drag_wing 
        compute.drag.parasite.fuselages            = Process_Geometry('fuselages')
        compute.drag.parasite.fuselages.fuselage   = Methods.Drag.parasite_drag_fuselage 
        compute.drag.parasite.propulsors           = Process_Geometry('propulsors')
        compute.drag.parasite.propulsors.propulsor = Methods.Drag.parasite_drag_propulsor # SZ
        #compute.drag.parasite.pylons               = Methods.Drag.parasite_drag_pylon
        compute.drag.parasite.total                = Common.Drag.parasite_total
        compute.drag.induced                       = Methods.Drag.induced_drag_aircraft
        compute.drag.miscellaneous                 = Methods.Drag.miscellaneous_drag_aircraft # different type used in FZ
        compute.drag.untrimmed                     = Common.Drag.untrimmed
        compute.drag.trim                          = Common.Drag.trim
        compute.drag.spoiler                       = Common.Drag.spoiler_drag
        compute.drag.total                         = Common.Drag.total_aircraft # SZ
        
        
    def initialize(self):
        """Initializes the surrogate needed for lift calculation.

        Assumptions:
        None

        Source:
        N/A

        Inputs:
        None

        Outputs:
        None

        Properties Used:
        self.geometry
        """            
        super(Supersonic_Zero, self).initialize()
        
        use_surrogate             = self.settings.use_surrogate
        include_slipstream_effect = self.settings.include_slipstream_effect
        vortex_distribution_flag  = self.settings.plot_vortex_distribution 
        n_sw                      = self.settings.number_panels_spanwise    
        n_cw                      = self.settings.number_panels_chordwise  
        
        self.process.compute.lift.inviscid_wings.geometry = self.geometry 
        self.process.compute.lift.inviscid_wings.initialize(use_surrogate , vortex_distribution_flag , n_sw ,  n_cw ,include_slipstream_effect )     
        
                
    finalize = initialize        
