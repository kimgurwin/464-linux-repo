#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Tue Jun 8 19:45:15 2021
@author: dankovacevich

Updated in 2025 to replace PyPDF2 with pypdf
"""

from zipfile import ZipFile
import re
import py_compile
import os
import sys
from pypdf import PdfReader
import imghdr
import subprocess
import csv

#-----------list of condition names-----------

pythonFile = f".*(.py)$"
pdfFile = f"(.pdf)$"
pngFile = f"(.png)$"
textFile = f"(.txt)$"


def UnixFileType(filename):
    return subprocess.check_output(
        ["file", "--mime-type", "-b", filename]
    ).decode().rstrip()


#----------Test For Readable Text File------------
def ReadableTextFile():
    def readabletext(filename):
        try:
            filetype = UnixFileType(filename)
            if filetype == "text/plain":
                return 'correct'
            else:
                return "Not a valid .txt file"
        except:
            return "Not a valid .txt file"
    return readabletext

ReadableTextFile = ReadableTextFile()


#----------Test For Readable PDF File------------
def ReadablePDFFile():
    def readablepdf(filename):
        try:
            filetype = UnixFileType(filename)
            if filetype == "application/pdf":
                return 'correct'
            else:
                return "Not a valid .pdf file"
        except:
            return "Not a valid .pdf file"
    return readablepdf

ReadablePDFFile = ReadablePDFFile()


#----------Test For Readable JPEG File------------
def ReadableJPEGFile():
    def readablejpg(filename):
        try:
            filetype = UnixFileType(filename)
            if filetype == "image/jpeg":
                return 'correct'
            else:
                return "Not a valid JPEG file"
        except:
            return "Not a valid JPEG file"
    return readablejpg

ReadableJPEGFile = ReadableJPEGFile()


#----------Test For Readable PNG File------------
def ReadablePNGFile():
    def readablepng(filename):
        try:
            filetype = UnixFileType(filename)
            if filetype == "image/png":
                return 'correct'
            else:
                return "Not a valid png file"
        except:
            return "Not a valid png file"
    return readablepng

ReadablePNGFile = ReadablePNGFile()


#----------Test For Readable MSWORD File------------
def ReadableMSWORDFile():
    def readableword(filename):
        try:
            filetype = UnixFileType(filename)
            if filetype in (
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ):
                return 'correct'
            else:
                return "Not a valid MS word document"
        except:
            return "Not a valid MS word document"
    return readableword

ReadableMSWORDFile = ReadableMSWORDFile()


#----------Test For Readable EXCEL File------------
def ReadableEXCELFile():
    def readableexcel(filename):
        try:
            filetype = UnixFileType(filename)
            if filetype in (
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ):
                return 'correct'
            else:
                return "Not a valid MS Excel file"
        except:
            return "Not a valid MS Excel file"
    return readableexcel

ReadableEXCELFile = ReadableEXCELFile()


#----------Test For Readable PPT File------------
def ReadablePPTFile():
    def readableppt(filename):
        try:
            filetype = UnixFileType(filename)
            if filetype in (
                "application/vnd.ms-powerpoint",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            ):
                return 'correct'
            else:
                return "Not a valid MS PPT file"
        except:
            return "Not a valid MS PPT file"
    return readableppt

ReadablePPTFile = ReadablePPTFile()


#----------Test For Readable HTML File------------
def ReadableHTMLFile():
    def readablehtml(filename):
        if filename.endswith("html"):
            return 'correct'
        else:
            return 'Not a valid html file'
    return readablehtml

ReadableHTMLFile = ReadableHTMLFile()


#----------Test For Readable CSS File------------
def ReadableCSSFile():
    def readablecss(filename):
        if filename.endswith("css"):
            return 'correct'
        else:
            return 'Not a valid css file'
    return readablecss

ReadableCSSFile = ReadableCSSFile()


#----------Test For Readable CSV File------------
def ReadableCSVFile():
    def readablecsv(filename):
        try:
            with open(filename, newline='') as file:
                _ = csv.reader(file)
            if filename.endswith("csv"):
                return 'correct'
            else:
                return 'Not a valid csv file'
        except:
            return 'Not a valid csv file'
    return readablecsv

ReadableCSVFile = ReadableCSVFile()


#--------------Test for Max Pages-----------------
def PDFMaxPages(num):
    def pdfpages(filename):
        try:
            with open(filename, 'rb') as file:
                reader = PdfReader(file)
                num_pages = len(reader.pages)
                if num_pages > num:
                    difference = num_pages - num
                    return f'Over Max ({num}) Pages By {difference}'
                else:
                    return 'correct'
        except:
            return 'Failed to Open File'
    return pdfpages


#--------------Test for File Size-----------------
def MaxFileSize(num):
    def filesize(filename):
        try:
            size = os.path.getsize(filename)
            if size > num:
                difference = size - num
                return f'Over Max ({num}) Bytes by {difference}'
            else:
                return 'correct'
        except:
            return 'Failed to Open File'
    return filesize


#---------------Test For Compilation---------------
def PythonThatCompiles():
    def pythontest(filename):
        try:
            py_compile.compile(filename, doraise=True)
        except:
            return 'Failed Compile Check'
        return 'correct'
    return pythontest

PythonThatCompiles = PythonThatCompiles()


#-------------Checks Specific Condition------------
def checkcondition(zipfile, filename, requirement):
    with ZipFile(zipfile, 'r') as my_zip:
        my_zip.extract(filename)
    return requirement(filename)
