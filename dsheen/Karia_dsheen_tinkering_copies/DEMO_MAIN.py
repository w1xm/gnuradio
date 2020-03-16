import time

filenames = ['beginning_working_new.py', 'survey.py', 'end.py']
with open('output_file.py', 'w') as outfile:
    for fname in filenames:
        with open(fname) as infile:
            outfile.write(infile.read())


#time.sleep(5)
execfile('output_file.py')

#!/usr/bin/python
#import output_file
