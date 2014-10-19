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
      info["SID"] = splitText[0].strip()[7:-8]

      #if the student is a employee, set there EID
      if splitText[1].strip()[7:-8] != "":
         info["EID"] = splitText[1].strip()[7:-8]
      else:
         info["EID"] = None

      #Set the affiliation (Student/staff)
      info["Affiliation"] = splitText[4].strip()[13:-14]

      #set the first name
      info["FirstName"] = splitText[6].strip()[15:-16]

      #set the last name
      info["LastName"] = splitText[7].strip()[14:-15]

      #set the college (Arts and Scineces.. ect)
      info["College"] = splitText[11].strip()[16:-17]

      #set their major
      info["Major"] = splitText[12].strip()[14:-15]

      #if they have a minor, set the minor
      if splitText[13].strip()[16:-17] != "":
         info["Minor"] = splitText[13].strip()[16:-17]
      else:
         info["Minor"] = None
      info["ClassStanding"] = splitText[14].strip()[15:-16]

      return info

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

else:
   print "Bad user. Check the username/password"