    #azimuth sun scan


    #usr/bin/python
    from galcoord import radec_to_altaz
    from galcoord import altaz_to_radec
    from galcoord import get_time
    from galcoord import get_sun_altaz
    import matplotlib.pyplot as plt
    import numpy as np

    int_time=10
    freq=tb.get_freq()/1000 #MHz
    freq_offset=tb.get_if_bandwidth_2()/1000. #MHz
    flo= freq-freq_offset
    fhi= freq+freq_offset
    num_chan=tb.get_num_channels()
    freq_range=np.linspace(flo, fhi, num_chan)
    folder='sunscan/'
    savetitle='sun_scan_vectors.txt'
    scan_offset=10 #distance in degrees on either side of the sun
    step=2

    def report(pos):
        print "Position: "+ str(pos)

    print 'Locating sun...'
    sun_altaz=get_sun_altaz()
    print 'Sun located at ' + str(sun_altaz[0]) + 'azimuth , ' + str(sun_altaz[1]) + ' elevation.'
    print 'Moving to sun location...'
    point(sun_altaz[0], sun_altaz[1])
    wait(10)
    print "Ready to scan."
    print ' '

    #do the survey
    sun_altaz=get_sun_altaz() #recheck sun again
    relative_az=(-1)*scan_offset #start at lower end of the scan

    az=sun_altaz[0]+relative_az # set azimuth and elevation
    el=sun_altaz[1]

    file=open(folder+savetitle, 'w')
    file.write('Integration time '+str(int_time)+' seconds. Center frequency '+str(freq)+' MHz. \n \n')
    file.write('Azimuth Elevation RA DEC Time Center Data_vector \n \n')

    while relative_az<=scan_offset: #azimuth loop

        #establish ra/dec for position
        radec=altaz_to_radec(az,el)
        ra=radec[0]
        dec=radec[1]

        #take data at current position and store
        point(az,el)
        wait(5)
        time=get_time() #so time will be the time at the start of the observation
        data=observe(int_time)
        file.write(str(az)+' ')
        file.write(str(el)+' ')
        file.write(str(ra)+' ')
        file.write(str(dec)+' ')
        file.write(str(time)+' ')
        file.write(str(data)+'\n \n')

        #create figure
        plt.figure()
        plt.title(str(round(az,2))+' '+str(round(el,2))+ ' '+ str(time))
        plt.xlabel('Frequency (MHz)')
        plt.ylabel('Power (W) *not calibrated')
        plt.plot(freq_range, data)
        plt.savefig(folder+'az'+str(relative_az)+'.pdf')
        print 'Data acquired.'
        wait(1)

        #update azimuth from recalculated sun position
        sun_altaz=get_sun_altaz()
        relative_az+=step
        az=sun_altaz[0]+relative_az
        el=sun_altaz[1]


    file.close()