#usr/bin/python

#gives the aziumuth and elevation for galactic coordinates
#position is the MIT radome
from astropy.utils import iers
iers.conf.iers_auto_url = "ftp://cddis.gsfc.nasa.gov/pub/products/iers/finals2000A.all"
#"https://datacenter.iers.org/data/9/finals2000A.all"
from astropy.coordinates import SkyCoord
from astropy.coordinates import Angle
from astropy.coordinates import ICRS
from astropy.coordinates import GCRS
from astropy.coordinates import Galactic
from astropy.coordinates import Galactocentric
from astropy.coordinates import UnitSphericalRepresentation
import astropy.coordinates as coord
from astropy import units as u
from astropy.constants import c
from astropy.time import Time
from astroplan import Observer
import numpy as np

coord.galactocentric_frame_defaults.set('latest')
from astroplan import download_IERS_A
download_IERS_A()

#from astroplan import FixedTarget
#Mars = FixedTarget.from_name("mars")

#observer-specific coordinates
mitlat=42.3601*u.degree
mitlong=-71.0942*u.degree
radome_elevation=100*u.m #roughly 100m above sea level

#define an observer and an altaz frame
radome_observer=Observer(latitude=mitlat,longitude=mitlong, elevation=radome_elevation, name='radome', timezone='US/Eastern')
icrs_frame=ICRS()
galactic_frame=Galactic()

#print radome_observer.sun_altaz(time)

HYDROGEN_FREQ = 1420.406*u.MHz

def freqs_to_vel(center_freq, fs, sc):
    """Convert frequency to radial Doppler velocity.

    Accounts for movement of the earth relative to the sun and the sun relative to galactic center.

    Args:
        center_freq: frequency at zero velocity
        fs: Quantity object representing frequencies
        sc: SkyCoord object representing one or many coordinates (must have obstime and location set)
    """

    # Convert from earth reference frame to solar reference frame using
    # https://docs.astropy.org/en/stable/coordinates/velocities.html#radial-velocity-corrections
    # Then convert from solar reference frame to Galactic Standard of Rest using
    # https://docs.astropy.org/en/stable/generated/examples/coordinates/rv-to-gsr.html
    pos_gal = sc.galactic
    v_to_bary = pos_gal.radial_velocity_correction(kind='barycentric')
    # Calculate the sun's velocity projected in the observing direction.
    v_sun = Galactocentric().galcen_v_sun.to_cartesian()
    cart_data = pos_gal.data.to_cartesian()
    unit_vector = cart_data / cart_data.norm()
    v_proj = v_sun.dot(unit_vector)

    doppler_shift = u.doppler_radio(center_freq)

    v_local = fs.to(u.km/u.s, doppler_shift)
    v_bary = v_local + v_to_bary + v_local * v_to_bary / c
    # v_bary is now barycentric; now we need to remove the solar system motion as well
    return (v_bary + v_proj)

def altaz_frame(time=None):
    if not time:
        time=Time.now()
    return radome_observer.altaz(time)

def get_time():
    time=Time.now()
    return time

def gcrs_to_altaz(ra,dec):
    gcrs_frame=update_GCRS()
    pos_gcrs=SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame=gcrs_frame)
    pos_altaz=pos_gcrs.transform_to(altaz_frame())
    return (pos_altaz.az.degree, pos_altaz.alt.degree)

def gal_to_altaz(lcoord,bcoord): #galactic coords in degrees
    #define a galactic position
    pos_gal=SkyCoord(l=lcoord*u.degree, b=bcoord*u.degree, frame='galactic')
    #transform the galactic position to an altaz one
    pos_altaz=pos_gal.transform_to(altaz_frame())
    #print(pos_altaz.to_string())
    return (pos_altaz.az.degree, pos_altaz.alt.degree)

def radec_to_altaz(ra,dec):
    pos_icrs=SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame=icrs_frame)
    pos_altaz=pos_icrs.transform_to(altaz_frame())
    return (pos_altaz.az.degree, pos_altaz.alt.degree)

def altaz_to_radec(az,el):
    #define the position
    pos_altaz=SkyCoord(az=az*u.degree, alt=el*u.degree, frame=altaz_frame())
    #transform to RA DEC
    pos_icrs=pos_altaz.transform_to(icrs_frame)
    return(pos_icrs.ra.degree, pos_icrs.dec.degree)


def altaz_to_gal(az, el):
    pos_altaz=SkyCoord(az=az*u.degree, alt=el*u.degree, frame=altaz_frame())
    pos_gal=pos_altaz.transform_to(galactic_frame)
    return (pos_gal.l.degree, pos_gal.b.degree)


def get_sun_altaz():
    time=Time.now()    #print time
    pos=radome_observer.sun_altaz(time)
    return (pos.az.degree, pos.alt.degree)

def get_moon_altaz():
    time=Time.now()    #print time
    pos=radome_observer.moon_altaz(time)
    return (pos.az.degree, pos.alt.degree)

#def get_mars_altaz():
#    time=Time.now()    #print time
#    pos=radome_observer.altaz(time,Target=Mars)
 #   return (pos.az.degree, pos.alt.degree)

# From AstroPy 4.0 (not compatible with Python 2.7)
def directional_offset_by(coord, position_angle, separation):
    slat = coord.represent_as(UnitSphericalRepresentation).lat
    slon = coord.represent_as(UnitSphericalRepresentation).lon

    newlon, newlat = offset_by(
        lon=slon, lat=slat,
        posang=position_angle, distance=separation)

    return SkyCoord(newlon, newlat, frame=coord.frame)

def offset_by(lon, lat, posang, distance):
    # Calculations are done using the spherical trigonometry sine and cosine rules
    # of the triangle A at North Pole,   B at starting point,   C at final point
    # with angles     A (change in lon), B (posang),            C (not used, but negative reciprocal posang)
    # with sides      a (distance),      b (final co-latitude), c (starting colatitude)
    # B, a, c are knowns; A and b are unknowns
    # https://en.wikipedia.org/wiki/Spherical_trigonometry

    cos_a = np.cos(distance)
    sin_a = np.sin(distance)
    cos_c = np.sin(lat)
    sin_c = np.cos(lat)
    cos_B = np.cos(posang)
    sin_B = np.sin(posang)

    # cosine rule: Know two sides: a,c and included angle: B; get unknown side b
    cos_b = cos_c * cos_a + sin_c * sin_a * cos_B
    # sin_b = np.sqrt(1 - cos_b**2)
    # sine rule and cosine rule for A (using both lets arctan2 pick quadrant).
    # multiplying both sin_A and cos_A by x=sin_b * sin_c prevents /0 errors
    # at poles.  Correct for the x=0 multiplication a few lines down.
    # sin_A/sin_a == sin_B/sin_b    # Sine rule
    xsin_A = sin_a * sin_B * sin_c
    # cos_a == cos_b * cos_c + sin_b * sin_c * cos_A  # cosine rule
    xcos_A = cos_a - cos_b * cos_c

    A = Angle(np.arctan2(xsin_A, xcos_A), u.radian)
    # Treat the poles as if they are infinitesimally far from pole but at given lon
    small_sin_c = sin_c < 1e-12
    if small_sin_c.any():
        # For south pole (cos_c = -1), A = posang; for North pole, A=180 deg - posang
        A_pole = (90*u.deg + cos_c*(90*u.deg-Angle(posang, u.radian))).to(u.rad)
        if A.shape:
            # broadcast to ensure the shape is like that of A, which is also
            # affected by the (possible) shapes of lat, posang, and distance.
            small_sin_c = np.broadcast_to(small_sin_c, A.shape)
            A[small_sin_c] = A_pole[small_sin_c]
        else:
            A = A_pole

    outlon = (Angle(lon, u.radian) + A).wrap_at(360.0*u.deg).to(u.deg)
    outlat = Angle(np.arcsin(cos_b), u.radian).to(u.deg)

    return outlon, outlat
