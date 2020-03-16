    #!/usr/bin/python

    def quitting():
        tb.stop()
        tb.wait()
    #    qapp.connect(qapp, Qt.SIGNAL("aboutToQuit()"), quitting)
    #    qapp.exec_()

    quitting()



if __name__ == '__main__':
    main()
