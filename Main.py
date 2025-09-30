#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#may need to install PyPDF2 to work
import re, sys, os
from Deliverable import *


zipfilename = sys.argv[1]
zfnm = re.match(f"(?P<year>202\d)-(?P<project>P[012])-(?P<team>\w+)-report.zip", zipfilename)             
if not zfnm:
    print('filename:', arg1, 'did not match the required pattern')
    sys.exit()
  
if not zfnm.group('team').lower() in {'maize', 'blue', 'red', 'green', 'purple'}:
   print('unknown team name:', zfre.group('team'))
    
   
globals().update(zfnm.groupdict()) 

zf = ZipFolder(zfnm.string)

#Right now supports check for (2nd - n parameter):
    #ReadableTextFile
    #ReadablePDFFile
    #ReadableJPEGFile
    #ReadablePNGFile
    #ReadableMSWORDFile
    #ReadableEXCELFile
    #ReadablePPTFile
    #ReadableHTMLFile
    #ReadableCSSFile
    #ReadableCSVFile
    #PDFMaxPages(n)
    #PythonThatCompiles
  
#If wish to check for type of file (first parameter):
    #pythonFile
    #pdfFile
    #pngFile
    #textFile
    
#Example of how to check:
'''
    src = Folder("src")
    src.mayHave("README.txt", ReadableTextFile)
    src.mayHave("OVERVIEW.txt", ReadableTextFile)
    src.mayHave(pythonFile, PythonThatCompiles)
    src.mustHave("USAGE.txt", ReadableTextFile)
    src.mustHave("INSTALL.txt", ReadableTextFile)
    zf.mustHave(src)
    zf.mustHave("COPYRIGHT.txt", ReadableTextFile)
    zf.mustHave("README.txt", ReadableTextFile)
    zf.mustHave(f"{year}-{project}-{team}-final.pdf",ReadableTextFile, PDFMaxPages(11))
    zf.mayHave(f"{year}-{project}-{team}-resources.pdf", ReadableTextFile)
    zf.mustHave(f"{year}-{project}-{team}-brainstorming.pdf", ReadableTextFile)
    zf.mustHave(f"{year}-{project}-{team}-team-photo.png", ReadableImageFile)
'''
zf.report()

