# Written by Ingar Arntzen, Motion Corporation

"""This implements utility function for calculations related to motion (MSV)"""

import math

# MSV
P,V,A,T = 0,1,2,3

##############################################
# UTILITY
##############################################

def has_real_solution(p,v,a,x):
    """Given motion determined from p,v,a. Determine if
    equation p(t) = p + vt + 0.5at^2 = x  for some real number t.

    The equation has real solution(s) if determinant 
    D = v^2-2a(p-x) >= 0.0
    """
    return True if  v*v - 2*a*(p-x) >= 0.0 else False

def get_real_solutions(p,v,a,x):
    """Given motion determined from p,v,a. Determine if
    equation p(t) = p + vt + 0.5at^2 = x  for some real number t.
    
    d = (-v (+/-)  sqrt[v^2 - 2a(p-x)])/a for a !=0
    d = (x-p)/v for a == 0

    """
    # No movement
    if a == 0.0 and v== 0.0:
        if p != x: return []
        else : return [0.0]  
    # Constant velocity
    if a== 0.0: return [(x-p)/v]
    # Constant Acceleration
    if not has_real_solution(p,v,a,x) : return []
    # Exactly one solution?
    discriminant = v*v - 2*a*(p-x)
    if discriminant == 0.0:
        return [-v/a]    
    sqrt = math.sqrt(discriminant)    
    d1 = (-v + sqrt)/a
    d2 = (-v - sqrt)/a
    # note that d1 or d2 may be -0.0 instead of 0.0
    return [min(d1,d2), max(d1,d2)]

def get_positive_real_solutions(p, v, a, x):
    """Given motion determined from p,v,a. Determine if
    equation p(t) = p + vt + 0.5at^2 = x  for some real number t.
    d = (-v (+/-)  sqrt[v^2 - 2a(p-x)])/a
    """
    return [x for x in get_real_solutions(p,v,a,x) if x > 0.0]

def get_min_positive_real_solution(p,v,a,x):
    """Find the smallest positive real solution. """
    solutions = get_positive_real_solutions(p,v,a,x)
    if solutions : return solutions[0]
    else : return None

def is_moving(v,a):
    """Calculates wheter a movement can be said to be moving. """
    return True if v !=0.0 or a != 0.0 else False

def compute_msv(vector, t):
    """
    This function computes the current msv given initial conditions
    and a time (t > t0)
    """
    p0,v0,a0,t0 = vector
    d = t - t0
    assert d >= 0, "Compute MSV with negative time delta %f" % d
    v = v0 +a0*d
    p = p0 + v0*d + 0.5*a0*d*d
    return (p, v, a0, t)

def get_position_within_range(p, min, max):
    """Check that min <= position <= max"""
    if min != None and max != None:
        assert min < max, "Illegal Range, MIN not less than MAX."
    # Position > MAX
    if max != None and p > max:
        p = max
    # Position < MIN
    elif min != None and p < min:
        p = min
    return p

def calculate_delta(vector, min, max):
    """Calculate how long it will take to reach MIN or MAX,
    given that the current motion is not interrupted."""    
    p,v,a,t = vector
    # time interval to hit MAX
    if max == None: delta_max = None
    else: delta_max = get_min_positive_real_solution(p,v,a, max)
    # time interval to hit MIN
    if min == None: delta_min = None
    else: delta_min = get_min_positive_real_solution(p,v,a, min)
    if delta_min != None and delta_max != None:
        if delta_min < delta_max:
            return delta_min, min
        else:
            return delta_max, max
    elif delta_min != None:
        return delta_min, min
    elif delta_max != None:
        return delta_max, max
    else:
        return None, None


def calculate_interval(vector, d):
    """Calculate the min, max positions of the smallest
    position-interval that contains the entire motion during the
    time-interval of length d seconds. The result is independent of
    vector[T], but be sure to give a fresh vector from msv.query() if
    the goal is to find the interval covered by an ongoing motion
    during the next d seconds.
    """
    p0, v0, a0 = vector[:3]
    if not is_moving(v0, a0):
        return (p0, p0)
    p1 = p0 + v0*d + 0.5*a0*d*d

    # general parabola
    # y = ax*x + bx + c
    # turning point (x,y) : x = - b/2a, y = -b*b/4a + c
    #
    # p_turning = 0.5*a0*d_turning*d_turning + v0*d_turning + p0
    # a = a0/2, b=v0, c=p0
    # turning point (d_turning, p_turning):
    # d_turning = -v0/a0
    # p_turning = p0 - v0*v0/(2*a0)

    if a0 != 0.0:
        d_turning = -v0/a0
        if 0 <= d_turning <= d:
            # turning point was reached p_turning is an extremal value            
            p_turning = p0 - 0.5*v0*v0/a0
            # a0 > 0 => p_turning minimum
            # a0 < 0 => p_turning maximum
            if a0 > 0:
                return (p_turning, max(p0,p1))
            else:
                return (min(p0,p1), p_turning)
        
    # no turning point or turning point was not reached 
    return (min(p0,p1), max(p0,p1))
   
def calculate_solutions_in_interval(vector, d, plist):
    """
    Find all intersects between a motion and a the positions given in
    plist, within a given interval. A single point may be intersected
    at 0,1 or 2 two different times (i.e. none, forwards, backwards).

    vector = (p0,v0,a0) describes the initial conditions of a motion 
    d gives the length of the time interval, in which the motion is considered
    plist is a list of floating-point positions.

    The following equation describes how position varies with time
    p(t) = 0.5*a0*t*t + v0*t + p0

    We solve this equation with respect to t, for all position values given in plist.  
    Only real solutions within the considered interval 0<=t<=d are returned.
    Solutions are returned sorted by time. 
    """
    solutions = []
    p0, v0, a0 = vector[:3]
    for p in plist:
        solutions+= [(t,p) for t in get_real_solutions(p0,v0,a0,p) if 0.0 <= t <= d]
    return sorted(solutions)
         

def compare_vectors(old_vector, new_vector):
    """Checks if the internal state of two msv's are equal."""
    p_equal = new_vector[P] == None or new_vector[P] == old_vector[P]
    v_equal = new_vector[V] == None or new_vector[V] == old_vector[V]
    a_equal = new_vector[A] == None or new_vector[A] == old_vector[A]
    t_equal = new_vector[T] == None or new_vector[T] == old_vector[T]
    return (p_equal, v_equal, a_equal, t_equal)



#################################################
# MAIN
#################################################

if __name__ == '__main__':

    def test_calculate_interval():

        vectors = [
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            (0.0, 0.0, -1.0),
            
            (0.0, 1.0, 0.0),
            (0.0, 1.0, 1.0),
            (0.0, 1.0, -1.0),
            
            (0.0, -1.0, 0.0),
            (0.0, -1.0, 1.0),
            (0.0, -1.0, -1.0),
            ]

        pos = [0.0, 1.0]
        vel = [0.0, 1.0, -1.0]
        acc = [0.0, 1.0, -1.0]

        delays = [0.0,1.0,2.0,3.0]
        for d in delays:
            for p in pos:
                for v in vel:
                    for a in acc:
                        t = (p,v,a)
                        print d, t, calculate_interval(t, d)
            print


    def test_calculate_solutions_in_interval():

        vector = (0.0, 1.0, -1.0)
        d = 3
        # covers interval [-1.5, 0.5]
        plist = [0.0, -1.5, 0.5, -2.0, 2.0, -0.5, 0.25]
        solutions = calculate_solutions_in_interval(vector, d, plist)
        
        # expected result: 
        expected = [(0.0, 0.0), ("?",0.25), ("?", 0.5), ("?", 0.25), ("?", 0.0), ("?", -0.5), (3.0,-1.5)]

        for i in range(len(expected)):
            print expected[i], "->", solutions[i]


    # test_calculate_interval()
    test_calculate_solutions_in_interval()
