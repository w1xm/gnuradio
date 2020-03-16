    #azimuth sun scan


    #usr/bin/python
    from galcoord import radec_to_altaz
    from galcoord import altaz_to_radec
    from galcoord import get_time
    from galcoord import get_moon_altaz
    import matplotlib.pyplot as plt
    import numpy as np

    int_time=5
    freq=tb.get_sdr_frequency()/1000000 #MHz
    freq_offset=tb.get_output_vector_bandwidth()/2000000. #MHz
    flo= freq-freq_offset
    fhi= freq+freq_offset
    num_chan=tb.get_num_channels()
    freq_range=np.linspace(flo, fhi, num_chan)
    folder='moon_contour/run3/'
    savetitle='moon_scan_vectors.txt'

    #scan parameters
    scan_sidelength=10 #distance in degrees across the sun
    scan_offset=scan_sidelength/2 #distance on either side
    step=2
    array_sidelength=int(scan_sidelength/step)+1

    #set up data array
    array=np.zeros((array_sidelength,array_sidelength))

    #Get in position for the scan
    print 'Locating moon...'
    moon_altaz=get_moon_altaz()
    print 'Moon located at ' + str(moon_altaz[0]) + 'azimuth , ' + str(moon_altaz[1]) + ' elevation.'
    print 'Moving to moon location...'
    point(moon_altaz[0], moon_altaz[1])
    wait(10)
    print "Ready to scan."
    print ' '

    #do the survey
    moon_altaz=get_moon_altaz() #recheck sun again
    relative_el=(-1)*scan_offset #start at low elevation
    el=moon_altaz[1]+relative_el

    i=0 #elevation in array
    j=0 #azimuth in array

    file=open(folder+savetitle, 'w')
    file.write('Integration time '+str(int_time)+' seconds. Center frequency '+str(freq)+' MHz. \n \n')
    file.write('Azimuth Elevation RA DEC Time Center Data_vector \n \n')

    while i<array_sidelength: #elevation loop

        j=0
        relative_az=(-1)*scan_offset
        az=moon_altaz[0]+relative_az
        while j<array_sidelength: #azimuth loop

            print "ELEVATION INDEX: "+str(i) + ' RELATIVE ELEVATION: ' + str(relative_el)
            print "AZIMUTH INDEX: " +str(j) + ' RELATIVE AZIMUTH: ' + str(relative_az)

            #establish ra/dec for position
            radec=altaz_to_radec(az,el)
            ra=radec[0]
            dec=radec[1]

            #take data at current position and store
            point(az,el)
            wait(6)
            time=get_time() #so time will be the time at the start of the observation
            data=observe(int_time)
            file.write(str(az)+' ')
            file.write(str(el)+' ')
            file.write(str(ra)+' ')
            file.write(str(dec)+' ')
            file.write(str(time)+' ')
            file.write(str(data)+'\n \n')

            #integrate
           # print data
            integrated=sum(data)
            array[i][j]=integrated
            print integrated
            #print array

            #create figure
            plt.figure()
            plt.title(str(round(az,2))+' '+str(round(el,2))+ ' '+ str(time))
            plt.xlabel('Frequency (MHz)')
            plt.ylabel('Power at Feed (W)')
            plt.plot(freq_range, data)
            plt.savefig(folder+'az'+str(relative_az)+'.pdf')
            plt.close()
            print 'Data acquired.'
            wait(1)

            #update azimuth from recalculated sun position
            moon_altaz=get_moon_altaz()
            relative_az+=step
            az=moon_altaz[0]+relative_az
            el=moon_altaz[1]+relative_el
            j+=1
        
        relative_el += step    
        el=moon_altaz[1]+relative_el
        i+=1


    file.write(str(array))

    file.close()

    print(array)
