#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  7 18:19:06 2021

@author: dankovacevich
"""

from zipfile import ZipFile
import re
import py_compile
import os
from Requirements import *
#from Main import out_put

class Folder:
  def __init__(self, foldername):

    # string
    # name of the folder
    self.foldername = foldername + "/"

    # array of two arrays
    # first array contains name of file
    # second array contains 
    self.folderrequirements = [] 

    # array of arrays
    # first item in subarray is the name of the optional file
    # the rest of the 
    self.folderoptional = []
  
  # INPUT
  #           file = a string or a filetype
  #   requirements = a list of conditions
  # EFFECTS
  #   adds file as an array to the list of folder requirements  
  #   adds conditions to the file array
  def mustHave(self, file, *requirements):
    self.folderrequirements.append([file])
    for condition in requirements:
      self.folderrequirements[-1].append(condition)

  # INPUT
  #           file = a string or a filetype
  #   requirements = a list of conditions
  # EFFECTS
  #   adds file as an array to the list of optional folders
  #   adds conditions to the file array
  def mayHave(self, file, *requirements):
    self.folderoptional.append([file])
    for condition in requirements:
      self.folderoptional[-1].append(condition)
        
    
               
class ZipFolder:
  #-----constructor that creates array of file names-----
  def __init__(self,zipfilename):

    # array of strings
    # contains names of files in zip folder
    self.files = []

    # array of strings
    # contains names of junk files
    self.junk = []

    # array of arrays
    # first item in subarray is name of file
    # the rest of the items are requirements
    self.requirements = []

    # array of arrays
    # first item in subarray is the name of the optional file
    # the rest of the items are the requirements for that file
    self.optional = []

    # array
    # contains names of correct
    self.correct = []

    # array of strings
    # contains errors
    self.errors = []

    # array of strings
    # contains names of missing deliverables
    self.missing = []

    # string
    # name of the zip folder
    self.zipfilename = zipfilename

    # array, content type doesn't matter
    # temporary variable used to keep track of errors within files
    self.errmsg = [] 

    # array, content type doesn't matter
    # temporary variable used to keep track of correct stuff in files
    self.crrmsg = [] 

    # array, content type doesn't matter
    # temporary variable used to keep track of missing files
    self.missng = [] 

    for name in ZipFile(zipfilename,'r').namelist():
      self.files.append(name)

    self.addFolders()

    # strings that hold the year, project number, and team color
    self.year = ''
    self.project = ''
    self.team = ''

  # EFFECTS
  #   reads through the file list, and looks for folders
  #   adds folder names to files
  def addFolders(self):
    for filepath in self.files:
      split_filepath = filepath.split('/')
      if len(split_filepath) > 1:
        if (split_filepath[0] + '/' not in self.files):
          self.files.append(split_filepath[0] + '/')
    
  # INPUT
  #           file = a string or a filetype
  #   requirements = a list of conditions. the file is a folder object, this is empty
  # EFFECTS
  #   adds file as an array to the list of folder requirements  
  #   adds conditions to the file array
  def mustHave(self, name, *requirements):
    self.requirements.append([name])
    for condition in requirements:
      self.requirements[-1].append(condition)
          
  # INPUT
  #           file = a string or a filetype
  #   requirements = a list of conditions. the file is a folder object, this is empty
  # EFFECTS
  #   adds file as an array to the list of optional folders
  #   adds conditions to the file array
  def mayHave(self, name, *requirements):
    self.optional.append([name])
    for condition in requirements:
      self.optional[-1].append(condition)

  # INPUT
  #   requirements = list of requirements
  # EFFECTS
  #   adds the requirements to all of the folders and files
  #   in the optional and required lists
  def mustAllHave(self, *requirements):
    for req in requirements:
      for file in self.optional:
        file.append(req)
      for file in self.requirements:
        file.append(req)


  # EFFECTS
  #   prints all files in the list of files  
  def printfiles(self):
    for i in self.files:
      print(i)
    print('\n')
      
  # INPUT
  #        folder = a folder object
  #    foldername = a string with name of the folder
  #   folder_reqs = a list of conditions that the folder must follow
  #         types = either 'r' or 'o' for requires or optional
  # EFFECTS
  #   iterates through folder_reqs. looks through the files in folder for the current
  #   item in folder_reqs. if there is a match, we have found that file and that is good.
  #   continue to check the rest of the reqs for that folder, including the files inside 
  def checkfolderrequirements(self, folder, foldername, folder_reqs, types):
    for k in range(0,len(folder_reqs)):
      foundfile = 0
      for l in range(0,len(self.files)):
        #if finds match
        if(re.match(foldername + folder_reqs[k][0], self.files[l])):
          foundfile = 1 
          #only requirement is name
          if(len(folder_reqs[k]) == 1):
            self.correct.append(foldername)
          else:
            try:
              self.foundfolderfilematch(self.files[l], folder_reqs[k], foldername, types)
            except Exception as e:
              print(e)
                  
      if(foundfile == 0 and types == 'r'):
        self.missng.append(folder.folderrequirements[k][0])

  # EFFECTS
  #   this function looks through all the file paths in the zip folder and returns errors if there are spaces
  def checkforspaces(self):
    for path in self.files:
      errmsg = [path]
      if ' ' in path:
        errmsg.append('contains a \' \' in its name')
      if len(errmsg) > 1:
        self.errors.append(errmsg)
      
      
  # INPUT
  #   folder = a folder object that we want to check
  #   types = either 'r' or 'o' for requires or optional
  # EFFECTS
  #   we are solely focused on this folder now, so set the error and correct message to 
  #   be the foldername. check whatever is optional or required for that folder.
  #   if there are errors/correct/missing append those to their respective arrays
  def foundfoldermatch(self, folder, types):
    foldername = folder.foldername
    self.errmsg = [foldername] 
    if(types == 'r'):    
      self.crrmsg = [foldername]
    elif(types == 'o'):
      fldrname = foldername.strip('/')
      fldrname += " (optional)/"
      self.crrmsg = [fldrname]
    self.missng = [foldername]
    self.checkfolderrequirements(folder, foldername, folder.folderrequirements, 'r')
    self.checkfolderrequirements(folder, foldername, folder.folderoptional, 'o')
    if(len(self.crrmsg) > 1):
      self.correct.append(self.crrmsg)
    if(len(self.errmsg) > 1 and types == 'r'):
      self.errors.append(self.errmsg)
    if(len(self.missng) > 1 and types == 'r'):
      self.missing.append(self.missng) 
          
  # INPUT
  #         file = a string with the file name
  #    file_reqs = a list with the name of the file to look for and the requirements
  #   foldername = the name of the folder we are looking in
  #        types = either 'r' or 'o' for requires or optional
  # EFFECTS 
  #   loops through the requirements of a file in a folder, and confirms them.
  #   strip the foldername from the file name. if there is an error, add that to the error message
  #   otherwise, add that file to the correct message
  def foundfolderfilematch(self, file, file_reqs, foldername, types):
    file_name = file
    founderror = 0
    #loops through all the requirements of a required file and confirms them
    for m in range(1, len(file_reqs)):
      result = checkcondition(self.zipfilename, file_name, file_reqs[m])
      os.remove(file_name)
      if(result != 'correct'):
        founderror = 1
        self.errmsg.append(file_name.strip(foldername))
        self.errmsg.append(result)
    if(founderror == 0):
      if(types == 'r'): 
        self.crrmsg.append(file_name.strip(foldername))
      elif(types == 'o'):
        self.crrmsg.append(file_name.strip(foldername) + " (optional)")
        
  #-----loops through requirements for individual file-----    
  # INPUT
  #    file = name of the file along with the requirements
  #   types = 'r' or 'o' for requires or optional
  # EFFECTS
  #   loops through all the requirements for a file, checks those. 
  #   if there are errors, append that to the errors
  def foundfilematch(self, file, types):
    #only requirement is file name
    if(len(file) == 1):
      self.correct.append(file[0])
    else:
      errmsg = []
      #loops through all the requirements of a required file and confirms them
      for k in range(1,len(file)):
        result = checkcondition(self.zipfilename, file[0], file[k])
        os.remove(file[0])
        if(result != 'correct'):
          errmsg.append(result)
      if(len(errmsg) == 0):
        if(types == 'o'):
          self.correct.append(file[0] + " (optional)")
        else:
          self.correct.append(file[0])
      else:
        self.errors.append([file[0]] + errmsg)
  
  # INPUT
  #   array = either self.requirements or self.optional
  #   types = 'r' or 'o' for requires or optional
  # EFFECTS
  #   loops through array of requirements. looks through the files for that requirement
  #   since the first requirement is always the folder name, this works. if the file is a folder,
  #   call foundfoldermatch to check the requirements for that folder
  #   if the file is a file, call foundfilematch to check the requirements for that file
  def checkrequirements(self, reqs, types):
      for i in range(0, len(reqs)):     
      #loop through all files in zip to check for that requirement
         foundmatch = 0
         for j in range(0, len(self.files)):
            #check if its a folder
            if(isinstance(reqs[i][0], Folder)):
                #check if found match of filename to requirement
                if(reqs[i][0].foldername == self.files[j]):    
                   foundmatch = 1
                   self.foundfoldermatch(reqs[i][0], types) 
                   #remove from junk array  
                   for l in range(len(self.files)):
                       if(self.files[l].startswith(reqs[i][0].foldername)):
                           self.junk[l] = 1
            #not a folder 
            else:
                #if file is a match 
                if(re.match(reqs[i][0], self.files[j])):
                    self.junk[j] = 1
                    foundmatch = 1
                    self.foundfilematch(reqs[i], types)        
         #file didn't match
         if(foundmatch == 0 and types == 'r'):
            if(isinstance(reqs[i][0], Folder)):
                self.missing.append(reqs[i][0].foldername)
            else:
                self.missing.append(reqs[i][0])     

  # EFFECTS
  #   prints all error/correct/missing messages to terminal
  def printtext(self):
    #------------print correct deliverables---------------
    
    print('Correct Deliverables: ')
    for i in self.correct:
       if(i[0].endswith('/') and len(i) > 1):
           print(i[0])
           for j in range(1,len(i)):
               print("  ", i[j])
       else:    
           print(i) 
    print('\n')

    
    
    #------------print incorrect deliverables---------------   
    print('\nErrors:')
    for i in self.errors:
       if(i[0].endswith('/') and len(i) > 1):
            print(i[0] + ' : ' + i[1])
            for j in range(1, len(i),2):
              try:
                print("  ", i[j], ": ", i[j+1])
              except:
                pass
       else:
            print(i[0], ": ", i[1])
    print('\n') 
    
    #------------print missing deliverables---------------       
    print('Missing Deliverables: ')
    for i in self.missing:
       if(i[0].endswith('/') and len(i) > 1 ):
           print(i[0])
           for j in range(1,len(i)):
               print("  ", i[j])
       else:  
           print(i)       
             
    
    #-------------------print junk--------------------
    print('\n')
    print("Junk Files: " )
    for i in range(len(self.junk)):
        if (self.junk[i] == 0):
            print(self.files[i])
  
  # EFFECTS
  #   generates HTML report with error/correct/missing messages
  def printhtml(self):
    #Open html report and write opening tags, define style
    f = open('Report.html','w')
    message = """ 
    <!DOCTYPE html>
    <html>
    <title>Deliverable Testing Tool </title> 
    
    <div>
      <h1>Deliverable Testing Tool Report</h1>
    </div>

    <body>
    """
    f.write(message)

    message = """
    <style>
      head {color:#000000; font-family: Tahoma, sans-serif;}
      
      div {display: flex; flex-direction: column; justify-content: center; text-align: center;}
      p {line-height: .6;}
      .tab {display: inline-block; margin-left: 25px;}
    </style>
    """
    f.write(message)

    # should go at line 395:
    # body {background-color: #white; color:#000000; font-family: Tahoma, sans-serif;}

    header = f"""
    <p>From the name of the zip file:
      <br></br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp
        Year : {self.year}</text>
      <br></br>&nbsp&nbsp
        Project : {self.project} 
      <br></br>&nbsp&nbsp&nbsp&nbsp
        Team : {self.team}
      <br></br>All filenames will be checked against these values.
      <br></br>
    </p>
    """
    
    f.write(header)
  #------------print correct deliverables---------------
    f.write("<p>")  
    f.write(""" 
    """) 
    f.write(" <b>Correct Deliverables:</b> <br></br>")  
    f.write(""" 
    """)
    for i in self.correct:
      if(i[0].endswith('/') and len(i) > 1):
        f.write(i[0] + "<br></br>")
        f.write("""
        """)
        f.write("""
        """)
        for j in range(1,len(i)):
          f.write("<span class=tab></span>" + i[j] + "<br></br>")
          f.write(""" 
          """)
      #  f.write(""" 
      #  """)
      else:    
        f.write(i + "<br></br>" )
        f.write(""" 
        """)
    f.write("</p>")
    f.write(""" 
    """)
    
  #------------print incorrect deliverables---------------   
    f.write("<p>")
    f.write(""" 
    """) 
    f.write("<b>Errors:</b>" + "<br></br>") 
    f.write(""" 
    """)
    for i in self.errors:
      if(i[0].endswith('/') and len(i) > 1):
        f.write(i[0] + " : " + i[1] + "<br></br>")
        f.write(""" 
        """)
        f.write(""" 
        """)
        for j in range(1, len(i),2):
          try:
            f.write("<span class=tab></span>" + i[j] + ": " + i[j+1] + "<br></br>")
            f.write(""" 
            """)
          except:
            pass
        f.write(""" 
        """)
      else:
        f.write(i[0] + ": " + i[1] + "<br></br>")
        f.write(""" 
        """)
    f.write("</p>")
    f.write(""" 
    """)
    
    #------------print missing deliverables---------------       
    f.write("<p>")
    f.write(""" 
    """)  
    f.write("<b>Missing Deliverables:</b> <br></br>")
    f.write(""" 
    """)  
    for i in self.missing:
      if(i[0].endswith('/') and len(i) > 1 ):
        f.write(i[0] + "<br></br>") 
        f.write(""" 
        """)
        f.write(""" 
        """) 
        for j in range(1,len(i)):
          f.write("<span class=tab></span>" + i[j] + "<br></br>")
          f.write(""" 
          """) 
        f.write(""" 
        """)
      else:        
        f.write(i + "<br></br>")
        f.write(""" 
        """)
    f.write("</p>")
    f.write(""" 
    """)

    #-------------------print junk--------------------
    f.write("<p>")
    f.write(""" 
    """) 
    f.write( "<b>Junk Files:</b> <br></br>")
    f.write(""" 
    """) 
    for i in range(len(self.junk)):
      if (self.junk[i] == 0):
        f.write(self.files[i] + "<br></br>")
        f.write(""" 
        """)
    f.write("</p>")
    f.write(""" 
    """)
   #-----------------print ending tags----------------
    message = """
    </body>
    </html>"""
    f.write(message)
    f.close()       

  # EFFECTS
  #   checks optional and required requirements for the zip file
  #   generates HTML and terminal reports
  def report(self):  
    #initialize junk
    self.junk = [0]*len(self.files)
    #checks requirements with required flag
    self.checkrequirements(self.requirements, 'r')
    #checks requirements with optional flag
    self.checkrequirements(self.optional, 'o')
    self.checkforspaces()
    
    #-------------------PRINT RESULT----------------------
    self.printtext()
    self.printhtml()
    
                
                
                
                
                
                
                
                
      
         