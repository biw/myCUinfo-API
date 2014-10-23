#make sure to install requests if you want to use this
#http://python-requests.org
import requests

#NOTE: Code only works with python2 for now, working on fixing it once I get
#the whole api made.


class cuSession(requests.sessions.Session):

   #get past the weird javascript redirects that mycuinfo uses to login
   def __init__(self, username, password):

      #start a session in requests
      session = requests.Session()

      #start the session url by going to mycuinfo first
      x = session.get('https://mycuinfo.colorado.edu')

      #split up the url to get the session url
      xsplit = x.text.split('<form id="')[1].split('action="')
      url = xsplit[1].split('" method="post"')

      #login to the site and move to the ping adress that we got with url
      payload = {'pf.username': username, 'pf.pass': password}
      z = session.post('https://ping.prod.cu.edu' + url[0], data=payload)

      #we are now on our final ping page
      finalSubUrl = "https://ping.prod.cu.edu/sp/ACS.saml2"
      RelayUrl = "https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/"

      #get the ping code to loggin
      finalSub = z.text.split('value=')[1][1:].split('"/>')[0]

      #set the first redirect, we must always go to the opening url
      payload2 = {"SAMLResponse": finalSub, "RelayState": RelayUrl}

      #send the final ping adress, once this is done we are logged in.
      final = session.post(finalSubUrl, data=payload2)

      #if the user/pass was bad, the url will not be correct
      if final.url != "https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/":
         self.valid = False
      else:
         self.valid = True

      #from here on, we are a regular user who has all the logged in cookies
      #we can do anything that a web user could (javascript not included)
      self.session = session

   #get the basic info of the user (name, student ID, Major, College, etc.)
   def info(self):

      #if the user is not logged in, error out, else go for it
      if self.valid == False:
         return False

      #set the url (break it up so the line isnt huge)
      url0 = "https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/?cmd=get"
      url1 = "CachedPglt&pageletname=ISCRIPT_CU_PROFILE_V2"
      url = url0 + url1

      #get the page
      pageLoad = self.session.get(url)

      #get the text (encode it unicode)
      pageText = pageLoad.text.encode("utf-8")

      #split the text up a few times till we just have the info
      splitText = pageText.split("<!--")[2][:-2].strip().split("\n")[2:-5]

      #create a blank dictonary to add to
      info = {}

      #set the student id (SID)
      info["SID"] = int(splitText[0].strip()[7:-8])

      #set a shift for students who also are employees
      EmployeeShift = 0

      #if the student is a employee, set there EID
      if splitText[1].strip() != "<demographicData>":
         info["EID"] = int(splitText[1].strip()[7:-8])
         EmployeeShift = 1
      else:
         info["EID"] = 0

      #Set the affiliation (Student/staff)
      info["Affiliation"] = splitText[3 + EmployeeShift].strip()[13:-14]

      #set the first name
      info["FirstName"] = splitText[5 + EmployeeShift].strip()[15:-16]

      #set the last name
      info["LastName"] = splitText[6 + EmployeeShift].strip()[14:-15]

      #set the college (Arts and Scineces.. ect)
      info["College"] = splitText[10 + EmployeeShift].strip()[16:-18]

      #set their major
      info["Major"] = splitText[11 + EmployeeShift].strip()[14:-15]

      #if they have a minor, set the minor
      if splitText[13].strip()[16:-17] != "":
         info["Minor"] = splitText[13].strip()[16:-17]
      else:
         info["Minor"] = None

      info["ClassStanding"] = splitText[13 + EmployeeShift].strip()[15:-16]

      return info

   def classes(self, term = "Fall2014"):

      #if the user is not logged in, error out, else go for it
      if self.valid == False:
         return False

      #split up the url so it fits on one line
      url0 = "https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/"
      url1 = "?cmd=getCachedPglt&pageletname=CU_STUDENT_SCHEDULE"
      url = url0 + url1

      #get the page text from the page (encode it utf-8)
      pageText = self.session.get(url).text.encode("utf-8")

      #split up the first part by the Course Schedule
      FallText = pageText.split("BLDR Campus - Course Schedule: Fall 2014")[1:]

      #then split it up by line (Sort of)
      FallText = FallText[0].split("<tr>")[2:]

      #split up the second part by the Course Info
      Fall2 = pageText.split("BLDR Campus - Course Information: Fall 2014")[1:]

      #split it up by line (sort of)
      Fall2 = Fall2[0].split("<tr>")[2:]

      #set a variable to go through
      i = 0

      #create a blank array for the class list
      ClassList = []

      #while there are things in the class list
      while FallText[i][0:4].strip() == "<td":

         #creat a temp class to add the info to later
         tempClass = {}

         #split up the text for the first line
         ClassLines = FallText[i].strip().split("\n")

         #split up the text for the second line (we use this a little)
         ClassLines2 = Fall2[i].strip().split("\n")

         #go through the length of the  ClassLines
         for ii in range(len(ClassLines)):

            #redefine what a line is
            line = ClassLines[ii]

            #define what line2 is
            if ii == len(ClassLines)-1:
               line2 = ClassLines[ii]
            else:
               line2 = ClassLines2[ii+1]

            #if the department is empty
            if "Department" not in tempClass:

               #set the department
               tempClass["Department"] = line[4:8]

               #set the Class Number (ClassCP)
               tempClass["ClassCP"] = line[9:13]

               #set the Section Number (ClassCS)
               tempClass["ClassCS"] = line[14:17]

            #if there is no class title
            elif "Title" not in tempClass:

               #get it form the second line
               line2 = line2.split("\n")

               #set the title
               tempClass["Title"] = line2[0][4:-5]

            #if we are on lines 2,4,5 or 7 do nothing
            elif ii == 2 or ii == 4 or ii == 5 or ii == 7:
               do = "nothing"

            #if there is no class time set
            elif "Days" not in tempClass:

               #set the class day
               tempClass["Days"] = line.split(">")[1].split("<")[0].strip()

               #set the class start time
               tempClass["StartTime"] = line.split(">")[2].split("<")[0].strip()

               #set the class end time
               tempClass["EndTime"] = line.split(">")[4].split("<")[0].strip()

               #set the class instructor
               tempClass["Instructor"] =line2.split(">")[1].split("<")[0][0:-12]

            #if there is no building set
            elif "Building" not in tempClass:

               #get the building and the room
               BuildingRoom = line.split(">")[2].split("<")[0].strip().split()

               #set the building
               tempClass["Building"] = BuildingRoom[0]

               #set the room
               tempClass["Room"] = BuildingRoom[1]

            #if there is no class status set yet
            elif "Status" not in tempClass:

               #set the class status
               tempClass["Status"] = line[4:-5]

               #if there are no credit infos
               if line2[19:-5] == "":

                  #set the number of credits to 0
                  tempClass["Credits"] = 0

               else:

                  #set the class credits
                  tempClass["Credits"] = int(line2[19:-5])

            #if there is no grade set
            elif "Grade" not in tempClass:

               #if there is no grade info
               if line[19:-5] == "":

                  #set the grade to none
                  tempClass["Grade"] = None

               else:

                  #set teh grade info from the class
                  tempClass["Grade"] = line[19:-5]

         #add the class to the classList
         ClassList.append(tempClass)

         #add one to the counter of classes
         i += 1

      #return the classList
      return ClassList

   #look up the books needed for any class
   def books(self, Department, CourseNumber, Section, term = "Fall2014"):

      #if the user is not logged in, error out, else go for it
      if self.valid == False:
         return False

      #set the term info, we made it a little nicer becuase CU uses nums to
      #set the term info. The move up by three/four every semester, so we can
      #use that forumual to change the term info to correct number for the API.
      if term == "Summer2014" or term == 2144:
         term = "2144"
      elif term == "Fall2014" or term == 2147:
         term = "2147"
      elif term == "Spring2015" or term == 2151:
         term = "2151"
      elif term == "Summer2015" or term == 2154:
         term = "2154"
      else:
         raise Exception("Error: Invalid Term")

      #simple check to see if the department is valid
      if len(Department) != 4:
         raise Exception("Error: Invalid Department")

      #simple check to see if Course Number is valid
      if len(CourseNumber) != 4:
         raise Exception("Error: Invalid CourseNumber")

      #simple check to see if Section Number is valid
      if len(Section) != 3:
         raise Exception("Error: Invalid Section (DO included leading 0s)")

      #now that all the check are there, we can start trying to get books

      #set the base url (split so the line isnt huge)
      baseUrl0 = "https://portal.prod.cu.edu/psc/epprod/UCB2/ENTP/s/WEBLIB_CU"
      baseUrl1 = "_SCHED.ISCRIPT1.FieldFormula.IScript_Get_Boulder_Books?"
      baseUrl = baseUrl0 + baseUrl1

      #set the inputs based on the method inputs
      course1 = "&course1=" + Department + CourseNumber
      section1 = "&section1=" + Section
      term1 = "&term1=" + term

      #we set a variable called session1, I have always found it to equal B
      session1 = "&session1=B"

      pageText = self.session.get(baseUrl+course1+section1+term1+session1).text

      #split the text up by "td", ignore the first item in list
      splitText = pageText.encode("utf-8").split("td")[1:]

      #create a counter & empty book list
      i = 0
      bookList = []

      #while loop deviding into 15, the amount of lines in a book
      while i < len(splitText)/15:

         #create a book dict to add to
         newbook = {}

         #create the start and end of the loop based on i
         ii = 16*i
         endRange = 16 * (i+1)

         #while the range is on one book
         while ii < endRange:

            #if there is not Author, add it
            if "Author" not in newbook:
               newbook["Author"] = splitText[ii][1:-2].strip()

            #if there is not Title, add it
            elif "Title" not in newbook:
               newbook["Title"] = splitText[ii][1:-2].strip()

            #if there is not Required, add it (bool)
            elif "Required" not in newbook:

               #if the site tells us the book is required
               if splitText[ii][18:-2].strip() == "Required":
                  newbook["Required"] = True
               else:
                  newbook["Required"] = False

            #if there is no Course, add it
            elif "Course" not in newbook:
               newbook["Course"] = splitText[ii][1:-2].strip()

            #if there is no ISBN, add it
            elif "ISBN" not in newbook:
               newbook["ISBN"] = splitText[ii][1:-2].strip()

            #if there is no New Price, add it
            elif "New Price" not in newbook:
               newbook["New Price"] = float(splitText[ii][1:-2].strip())

            #if there is no Used Price, add it
            elif "Used Price" not in newbook:
               if len(splitText[ii][1:-2]) > 0:
                  newbook["Used Price"] = float(splitText[ii][1:-2].strip())
               else:

                  #if there is no price listed, set to N/A
                  newbook["Used Price"] = None

            #if there is no Rent Price, add it
            elif "Rent Price" not in newbook:
               if len(splitText[ii][1:-2]) > 2:
                  newbook["Rent Price"] = float(splitText[ii][1:-2].strip())
               else:

                  #if there is no price listed, set to N/A
                  newbook["Rent Price"] = None

            #increase ii by two (every other line has garbage text)
            ii += 2

         #append our newbook to the bookList
         bookList.append(newbook)

         #increase to the next book
         i +=1

      return bookList


#define the username & password for the cuSession
user0 = "user0000"
pass0 = "password"

#create the cuLog Session
cuLog = cuSession(user0, pass0)


#if the loggin session is a valid one
if cuLog.valid:

   #example of how to get the books from CSCI 2700, Section 010 (Fall 2014)
   print cuLog.books("CSCI", "2270", "010")

   #example of how to get the info of the user
   print cuLog.info()

   #example of how to get the classes of the user (Fall 2014)
   print cuLog.classes()

else:
   print "Bad user. Check the username/password"