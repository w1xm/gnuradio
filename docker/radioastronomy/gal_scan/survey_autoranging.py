# Prepare for Python 3
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from galcoord import gal_to_altaz
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from galcoord import get_time
import os.path
import time
import csv

#convert frequency f to radial velocity at galactic coordinate l
#account for movement of the sun relative to galactic center
def freq_to_vel(center_freq, f,l):
    c=2.998e5 #km/s
    v_rec=(center_freq-f)*c/center_freq
    v_sun=220 #km/s
    correction=v_sun*np.sin(np.deg2rad(l))
    return v_rec+correction

def run_survey(tb, point, savefolder, int_time=30, l_start=0, l_stop=360, l_step=2.5):
    gain=60
    tb.set_sdr_gain(gain)
    freq=tb.get_sdr_frequency()/1000000 #MHz
    freq_offset=tb.get_output_vector_bandwidth()/2000000. #MHz
    flo= freq-freq_offset
    fhi= freq+freq_offset
    num_chan=tb.get_num_channels()
    freq_range=np.linspace(flo, fhi, num_chan)

    #########################################
    # BEGIN COMMANDS #
    #########################################
    large_step=1 #signals that the dish just moved a bunch and we need to wait longer for it to settle

    #point at galactic center and give time to settle
    l=l_start
    #print('Moving to initial galactic longitude l=%f' % (l,))
    # pos=gal_to_altaz(l,0)
    # # while pos[1] <= 0:
    # #     pos=gal_to_altaz(l,0)
    # #     if pos[1] > 0: break
    # #     if l > l_stop: break
    # point(pos[0],pos[1])
    # wait(10)

    #do the survey
    file=open(os.path.join(savefolder, 'vectors.txt'), 'w')
    csvwriter = csv.writer(open(os.path.join(savefolder, 'vectors.csv'), 'w'))
    file.write('Integration time '+str(int_time)+' seconds. Center frequency '+str(freq)+' MHz. \n \n')
    csvwriter.writerow(['# Integration time: %d seconds Center frequency: %f MHz' % (int_time, freq)])
    csvwriter.writerow(['time', 'azimuth', 'elevation', 'RA', 'DEC'] + [str(f) for f in freq_range]*2)
    file.write('Azimuth Elevation RA DEC Time Center Data_vector \n \n')

    contour_longs = []
    contour_vels = []
    contour_data = []

    while l<=l_stop:
        #take data at a position
        pos=gal_to_altaz(l,0)
        if pos[1] > 0:
            print('Moving to galactic longitude l=' + str(l))
            point(pos[0],pos[1])
            if large_step:
                time.sleep(10)
            else:
                time.sleep(2)
            large_step=0

            print("Observing at galactic coordinates ("+str(l)+', 0).')
            apytime=get_time()
            data=tb.observe(int_time)

            #write to file
            file.write(str(l)+' ')
            file.write(str(0)+' ')
            file.write(str(apytime)+' ')
            file.write(str(data)+'\n \n')

            vel_range=np.array([freq_to_vel(freq, f,l) for f in freq_range])
            contour_longs.append(np.full(len(freq_range), l))
            contour_vels.append(vel_range)
            contour_data.append(data)

            apytime.format = 'fits'
            csvwriter.writerow([str(apytime), str(pos[0]), str(pos[1]), str(l), str(0)] + [str(f) for f in vel_range] + [str(f) for f in data])

            #frequency binned figure
            plt.figure()
            plt.title('l='+str(l)+ ' '+ str(apytime))
            plt.xlabel('Frequency (MHz)')
            plt.ylabel('Power at Feed (W/Hz)')
            plt.axvline(x=freq, color='black', ls='--')
            plt.ticklabel_format(useOffset=False)
            plt.plot(freq_range, data)
            plt.savefig(os.path.join(savefolder, 'lat'+str(l)+'_freq.pdf'))
            #time.sleep(1)
            plt.close()

            #velocity binned figure
            center_vel=freq_to_vel(freq, freq,l)

            plt.figure()
            plt.title('l='+str(l)+ ' '+ str(apytime))
            plt.xlabel('Velocity (km/s)')
            plt.ylabel('Power at Feed (W)')
            plt.axvline(x=0, color='black', ls='--')
            plt.ticklabel_format(useOffset=False)
            plt.plot(vel_range, data)
            plt.savefig(os.path.join(savefolder, 'lat'+str(l)+'_vel.pdf'))
            #time.sleep(1)
            plt.close()

            print('Data logged.')
            print()

        else:
            large_step=1

        l+=l_step
        if l >= l_stop: break

        #move to next position
        # pos=gal_to_altaz(l,0)
        # point(pos[0],pos[1])
        # wait(2)

    file.close()

    contour_vels = np.array(contour_vels)
    contour_longs = np.array(contour_longs)
    contour_data = np.array(contour_data)

    np.save(os.path.join(savefolder, 'contour_vels.npy'), contour_vels)
    np.save(os.path.join(savefolder, 'contour_longs.npy'), contour_longs)
    np.save(os.path.join(savefolder, 'contour_data.npy'), contour_data)

    plt.figure()
    plt.ylabel('Velocity (km/s)')
    plt.xlabel('Galactic Longitude')
    plt.ticklabel_format(useOffset=False)
    plt.contourf(contour_longs, contour_vels, contour_data, 100, vmin=0.8e-16, vmax=3e-16)
    plt.savefig(os.path.join(savefolder, '2d_contour.pdf'))
    #time.sleep(1)
    plt.close()

    plt.figure()
    plt.ylabel('Velocity (km/s)')
    plt.xlabel('Galactic Longitude')
    plt.ticklabel_format(useOffset=False)
    plt.pcolormesh(contour_longs, contour_vels, contour_data, vmin=0.8e-16, vmax=3e-16)
    plt.savefig(os.path.join(savefolder, '2d_mesh.pdf'))
    #time.sleep(1)
    plt.close()
