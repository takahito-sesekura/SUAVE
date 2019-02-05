## @ingroup Methods-Missions-Segments-Transition
# Constant_Accelerated_Climb_Constant_Angle.py
# 
# Created:  Feb 2019, M. Clarke

# ----------------------------------------------------------------------
#  Initialize Conditions
# ----------------------------------------------------------------------
from scipy.optimize import fsolve

## @ingroup Methods-Missions-Segments-Transition
def initialize_conditions(segment):
    """Sets the specified conditions which are given for the segment type.

    Assumptions:
    Constant acceleration and constant altitude

    Source:
    N/A

    Inputs:
    segment.altitude                [meters]
    segment.air_speed_start         [meters/second]
    segment.air_speed_end           [meters/second]
    segment.acceleration            [meters/second^2]
    conditions.frames.inertial.time [seconds]

    Outputs:
    conditions.frames.inertial.velocity_vector  [meters/second]
    conditions.frames.inertial.position_vector  [meters]
    conditions.freestream.altitude              [meters]
    conditions.frames.inertial.time             [seconds]

    Properties Used:
    N/A
    """      
    
    # unpack
    alt0        = segment.altitude_start 
    altf        = segment.altitude_end 
    climb_angle = segment.climb_angle
    v0          = segment.air_speed_start_vector
    vf          = segment.air_speed_end_vector
    ta0         = segment.thrust_angle_start  
    taf         = segment.thrust_angle_end  #***check**** segment.state.unknowns.thrust_angle_end 
    ax          = segment.acceleration   
    T0          = segment.pitch_initial
    Tf          = segment.pitch_final     
    t_nondim    = segment.state.numerics.dimensionless.control_points
    conditions  = segment.state.conditions 
    
    # check for initial altitude
    if alt is None:
        if not segment.state.initials: raise AttributeError('altitude not set')
        alt = -1.0 * segment.state.initials.conditions.frames.inertial.position_vector[-1,2]
        segment.altitude = alt
        
    # check for initial pitch
    if T0 is None:
        T0  =  segment.state.initials.conditions.frames.body.inertial_rotations[-1,1]
        segment.pitch_initial = T0    
        
    # check for initial velocity vector
    if v0 is None:
        v0  =  segment.state.initials.conditions.frames.inertial.velocity_vector[-1,:] 
        segment.velocity_vector = v0  
        
    # discretize on altitude
    alt = t_nondim * (altf-alt0) + alt0        
        
    # check for climb angle     
    if climb_angle is None:
        raise AttributeError('set climb')
    
    ground_distance = abs((altf-alt0)*np.arctan(climb_angle))
    true_distance   = sqrt((altf-alt0)**2 + ground_distance**2)
    t_initial       = conditions.frames.inertial.time[0,0]       
    vf_mag          = np.linalg.norm(vf)
    v0_mag          = np.linalg.norm(v0)
    
    if vf != None and ax != None:        
        elapsed_time = fsolve(func(x,true_distance,v0,ax),5) # initial guess of 5 seconds 
        # recalculated final velocity based on accleration 
        vf_mag = v0_mag + ax* (elapsed_time)
    
    if vf is None:
        if ax is None: raise AttributeError('set either final speed or acceleration')
        else:
            elapsed_time = fsolve(func(x,true_distance,v0,ax),5) # initial guess of 5 seconds 
            vf_mag = v0_mag + ax* (elapsed_time)
        
    if ax is None:
        if vf is None: raise AttributeError('set either final speed or acceleration')
        else:
            ax = (vf_mag**2 - v0_mag**2)/(2*true_distance)
            elapsed_time = (vf_mag - v0_mag)/ax     
    
    # dimensionalize time        
    t_final   = t_initial + elapsed_time
    t_nondim  = segment.state.numerics.dimensionless.control_points
    time      = t_nondim * (t_final-t_initial)
    
    # Figure out vx
    V  = (vf_mag-v0_mag) + v0_mag
    vx = t_nondim *  V  * np.cos(climb_angle)
    vz = t_nondim *  V  * np.sin(climb_angle)
    
    # set the body angle
    body_angle =time*(Tf-T0)/(t_final-t_initial)
    segment.state.conditions.frames.body.inertial_rotations[:,1] = body_angle[:,0]     
    
    # pack
    segment.state.conditions.freestream.altitude[:,0] = alt
    segment.state.conditions.frames.inertial.position_vector[:,2] = -alt # z points down
    segment.state.conditions.frames.inertial.velocity_vector[:,0] = vx 
    segment.state.conditions.frames.inertial.velocity_vector[:,2] = vz 
    segment.state.conditions.frames.inertial.time[:,0] = time[:,0]
    
def func(t,true_distance,v0,ax):      
    return true_distance - v0*t + 0.5*ax*(t**2)

# ----------------------------------------------------------------------
#  Residual Total Forces
# ----------------------------------------------------------------------
    
## @ingroup Methods-Missions-Segments-Cruise    
def residual_total_forces(segment):
    """ Calculates a residual based on forces
    
        Assumptions:
        The vehicle is not accelerating, doesn't use gravity
        
        Inputs:
            segment.acceleration                   [meters/second^2]
            segment.state.ones_row                 [vector]
            state.conditions:
                frames.inertial.total_force_vector [Newtons]
                weights.total_mass                 [kg]
            
        Outputs:
            state.conditions:
                state.residuals.forces [meters/second^2]

        Properties Used:
        N/A
                                
    """      
    
    # Unpack
    FT      = segment.state.conditions.frames.inertial.total_force_vector
    ax      = segment.acceleration 
    m       = segment.state.conditions.weights.total_mass  
    one_row = segment.state.ones_row
    
    a_x    = ax*one_row(1)
    
    # horizontal
    segment.state.residuals.forces[:,0] = FT[:,0]/m[:,0] - a_x[:,0]
    # vertical
    segment.state.residuals.forces[:,1] = FT[:,2]/m[:,0] 

    return
