    #for scanning the whole sky


    #usr/bin/python
    from galcoord import altaz_to_radec
    from galcoord import get_time
    import matplotlib.pyplot as plt
    import numpy as np

    int_time=5
    freq=tb.get_sdr_frequency()/1000000 #MHz
    freq_offset=tb.get_output_vector_bandwidth()/2000000. #MHz
    flo= freq-freq_offset
    fhi= freq+freq_offset
    num_chan=tb.get_num_channels()
    freq_range=np.linspace(flo, fhi, num_chan)
    folder='full_scans/run12/'
    savetitle='full_scan_vectors.txt'
    el_lower_limit=0
    el_upper_limit=75
    az_start=0
    az_stop=360
    az_step=20
    el_step=2.5

    def report(pos):
        print "Position: "+ str(pos)

    print 'Pointing at start point.'
    point(az_start, el_lower_limit)
    wait(10)
    print("Begin scan.")

    #do the survey
    el=el_lower_limit
    time=get_time()
    file=open(folder+savetitle, 'w')
    file.write('Integration time '+str(int_time)+' seconds. Center frequency '+str(freq)+' MHz. \n \n')
    file.write('Azimuth Elevation RA DEC Time Data_vector \n \n')
    while el<=el_upper_limit: #elevation loop
	az=az_start
	wait(10)
        while az<=az_stop: #azimuth loop

            #establish ra/dec for position
            radec=altaz_to_radec(az,el)
            ra=radec[0]
            dec=radec[1]

            #take data at current position and store
            point(az,el)
            wait(5) #wait to stabilize
            time=get_time() #so time will be the time at the start of the observation
            data=observe(int_time)
            file.write(str(az)+' ')
            file.write(str(el)+' ')
            file.write(str(ra)+' ')
            file.write(str(dec)+' ')
            file.write(str(time)+' ')
            file.write(str(data)+'\n \n')
            print('Data acquired.')

            #create figure
            #plt.figure()
            #plt.title(str(az)+' '+str(el)+ ' '+ str(time))
            #plt.xlabel('Frequency (MHz)')
            #plt.ylabel('Power W/Hz')
            #plt.axvline(x=1420.406, color='black', ls='--')
            #plt.ticklabel_format(useOffset=False)
            #plt.plot(freq_range, data)
            #plt.savefig(folder+str(az)+'_'+str(el)+'.pdf')
            #plt.close()
            wait(1)

            #update azimuth
            az+=az_step

        #update elevation
        el+=el_step

    file.close()
