
    #usr/bin/python
    from galcoord import gal_to_altaz
    import matplotlib.pyplot as plt
    from galcoord import get_time
    
    freq=tb.get_sdr_frequency()/1000000 #MHz
    freq_offset=tb.get_output_vector_bandwidth()/2000000. #MHz
    flo= freq-freq_offset
    fhi= freq+freq_offset
    num_chan=tb.get_num_channels()
    freq_range=np.linspace(flo, fhi, num_chan)

    #convert frequency f to radial velocity at galactic coordinate l
    #account for movement of the sun relative to galactic center
    def freq_to_vel(f,l):
        c=2.998e5 #km/s
        v_rec=(freq-f)*c/freq
        v_sun=220 #km/s
        correction=v_sun*np.sin(np.deg2rad(l))
        return v_rec+correction


    ############ Editable variables ###########
    savefolder='Galactic_survey_data/run2/'
    savetitle='vectors.txt'
    int_time=60
    l_start=0
    l_stop=90
    l_step=5
    #########################################
    # BEGIN COMMANDS #
    #########################################

    l=l_start
    print 'Moving to initial galactic longitude l=' + str(l)
    #point at galactic center and give time to settle
    pos=gal_to_altaz(l,0)
    point(pos[0],pos[1])
    wait(10)

    #do the survey
    file=open(savefolder+savetitle, 'w')
    file.write('Integration time '+str(int_time)+' seconds. Center frequency '+str(freq)+' MHz. \n \n')
    file.write('Azimuth Elevation RA DEC Time Center Data_vector \n \n')
    while l<=l_stop:
    	#take data at current position
        print "Observing at galactic coordinates ("+str(l)+', 0).'
        time=get_time()
    	data=observe(int_time) 

        #write to file
        file.write(str(l)+' ')
        file.write(str(0)+' ')
        file.write(str(time)+' ')
        file.write(str(data)+'\n \n')

        #frequency binned figure
    	plt.figure()
        plt.title('l='+str(l)+ ' '+ str(time))
    	plt.xlabel('Frequency (MHz)')
        plt.ylabel('Uncalibrated power (W)')
        plt.axvline(x=freq, color='black', ls='--')
        plt.ticklabel_format(useOffset=False)
        plt.plot(freq_range, data)
        plt.savefig(savefolder+'lat'+str(l)+'_freq.pdf')
        wait(1)
        plt.close()

        #velocity binned figure
        vel_range=np.array([freq_to_vel(f,l) for f in freq_range])

        plt.figure()
        plt.title('l='+str(l)+ ' '+ str(time))
        plt.xlabel('Velocity (km/s)')
        plt.ylabel('Uncalibrated power (W)')
        plt.axvline(x=0, color='black', ls='--')
        plt.ticklabel_format(useOffset=False)
        plt.plot(vel_range, data)
        plt.savefig(savefolder+'lat'+str(l)+'_vel.pdf')
        wait(1)
        plt.close()

        print 'Data logged.'
        print ' '

        l+=l_step
        if l > l_stop: break

        #move to next position
        pos=gal_to_altaz(l,0)
        point(pos[0],pos[1])
        wait(4)

    file.close()





