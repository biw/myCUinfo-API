#!/usr/bin/python
# coding=utf8
import requests


class cuSession(requests.sessions.Session):

    # get past the weird javascript redirects that mycuinfo uses to login
    def __init__(self, username, password):

        # start a session in requests
        session = requests.Session()

        # start the session url by going to mycuinfo first
        x = session.get('http://mycuinfo.colorado.edu')

        # split up the url to get the session url
        xsplit = x.text.split('<form id="')[1].split('action="')
        url = xsplit[1].split('" method="post"')

        # login to the site and move to the ping adress that we got with url
        payload = {'pf.username': username, 'pf.pass': password}
        z = session.post('https://ping.prod.cu.edu' + url[0], data=payload)

        # we are now on our final ping page
        finalSubUrl = "https://ping.prod.cu.edu/sp/ACS.saml2"
        RelayUrl = "https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/"

        # get the ping code to loggin
        finalSub = z.text.split('value=')[1][1:].split('"/>')[0]

        # set the first redirect, must always go to the opening url
        payload2 = {"SAMLResponse": finalSub, "RelayState": RelayUrl}

        # send the final ping adress, once this is done we are logged in.
        final = session.post(finalSubUrl, data=payload2)

        # if the user/pass was bad, the url will not be correct
        if final.url != "https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/":
            self.valid = False
        else:
            self.valid = True

        # from here on, we are a regular user who has all the logged in cookies
        # we can do anything that a web user could (javascript not included)
        self.session = session

    # get the basic info of the user (name, student ID, Major, College, etc.)
    def info(self):

        # if the user is not logged in, error out, else go for it
        if self.valid == False:
            return False

        # set the url (break it up so the line isnt huge)
        url0 = "https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/?cmd=get"
        url1 = "CachedPglt&pageletname=ISCRIPT_CU_PROFILE_V2"
        url = url0 + url1

        # get the page
        pageLoad = self.session.get(url)

        # get the text (encode it unicode)
        pageText = pageLoad.text

        # split the text up a few times till we just have the info
        splitText = pageText.split("<!--")[1][:-2].strip().split("\n")[2:-5]

        # create a blank dictonary to add to
        info = {}

        # set the student id (SID)
        try:
            info["sid"] = int(splitText[0].strip()[7:-8])
        except:
            print(len(splitText))

        # set a shift for students who also are employees
        employeeShift = 0

        # if the student is a employee, set there EID
        if splitText[1].strip() != "<demographicData>":
            info["eid"] = int(splitText[1].strip()[7:-8])
            employeeShift = 1
        else:
            info["eid"] = 0

        # Set the affiliation (Student/staff)
        info["affiliation"] = splitText[3 + employeeShift].strip()[13:-14]

        # set the first name
        info["firstName"] = splitText[5 + employeeShift].strip()[15:-16]

        # set the last name
        info["lastName"] = splitText[6 + employeeShift].strip()[14:-15]

        # set the college (Arts and Scineces.. ect)
        info["college"] = splitText[10 + employeeShift].strip()[16:-18]

        # set their major
        info["major"] = splitText[11 + employeeShift].strip()[14:-15]

        # if they have a minor, set the minor
        if splitText[13].strip()[16:-17] != "":
            info["minor"] = splitText[13].strip()[16:-17]
        else:
            info["minor"] = None

        info["classStanding"] = splitText[13 + employeeShift].strip()[15:-16]

        return info

    def classes(self, term="Fall 2015"):

        # if the user is not logged in, error out, else go for it
        if self.valid == False:
            return False

        # split up the url so it fits on one line
        url0 = "https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/"
        url1 = "?cmd=getCachedPglt&pageletname=CU_STUDENT_SCHEDULE"
        url = url0 + url1

        # get the page text
        pageText = self.session.get(url).text

        # split up the first part by the Course Schedule
        try:
            fallText = pageText.split("Grades / Details: " + term)[1].split(
                "* FCQ = Faculty Course Questionnaire")[0]
        except:
            print("Invalid term given for classes. Valid Ex: 'Fall 2015'")
            return None

        classInfoList = fallText.split("<tr>")[2:]

        classList = []

        for classInfo in classInfoList:

            # a lot of html parsing and spliting. Really hard to leave a nice
            # context without looking at the html. Tried to write so things
            # won't get wonky if values are blank

            tempClass = {}

            courseSection = classInfo[5:].split("&nbsp;")

            tempClass["department"] = courseSection[0]
            tempClass["classCode"] = courseSection[1][:4]
            tempClass["section"] = courseSection[1][5:8]

            nameAndType = classInfo.split("<td>")[2].split("</td>")[0]
            nameAndType = nameAndType.split("&nbsp;")

            tempClass["name"] = nameAndType[0].replace("&amp;", "&")
            tempClass["type"] = nameAndType[1][1:-1]

            dateAndTime = classInfo.split(
                "meetingtime\"")[1][1:].split("</div>")[0].split(">")

            tempClass["days"] = dateAndTime[0].split("<")[0][:-1]
            tempClass["startTime"] = dateAndTime[1].split("<")[0]
            tempClass["endTime"] = dateAndTime[3].split("<")[0]

            tempInstructor = {}

            instrutr = classInfo.split("iname=")[1].split("\"")[0].split(",")

            tempInstructor["firstName"] = instrutr[1]
            tempInstructor["lastName"] = instrutr[0]

            tempClass["instructor"] = tempInstructor

            extraInfo = classInfo.split("align=\"center\">")

            tempClass["credits"] = int(extraInfo[2].split("<")[0])
            tempClass["status"] = extraInfo[3].split("<")[0]
            tempClass["grade"] = extraInfo[4].split("<")[0]

            if tempClass["grade"] == "":
                del(tempClass["grade"])

            classList.append(tempClass)

        return classList

    # look up the books needed for any class
    def books(self, Department, CourseNumber, Section, term="Fall2015"):

        # if the user is not logged in, error out, else go for it
        if self.valid == False:
            return False

        # set the term info, we made it a little nicer becuase CU uses nums to
        # set the term info. The move up by three/four every semester, so we can
        # use that forumual to change the term info to correct number for the
        # API.
        if term == "Fall2015" or term == 2147:
            term = "2157"
        elif term == "Spring2015" or term == 2151:
            term = "2151"
        elif term == "Summer2015" or term == 2154:
            term = "2154"
        else:
            raise Exception("Error: Invalid Term")

        # simple check to see if the department is valid
        if len(Department) != 4:
            raise Exception("Error: Invalid Department")

        # simple check to see if Course Number is valid
        if len(CourseNumber) != 4:
            raise Exception("Error: Invalid CourseNumber")

        # simple check to see if Section Number is valid
        if len(Section) != 3:
            raise Exception("Error: Invalid Section (DO included leading 0s)")

        # now that all the check are there, we can start trying to get books

        # set the base url (split so the line isnt huge)
        baseUrl0 = "https://portal.prod.cu.edu/psc/epprod/UCB2/ENTP/s/WEBLIB_CU"
        baseUrl1 = "_SCHED.ISCRIPT1.FieldFormula.IScript_Get_Boulder_Books?"
        baseUrl = baseUrl0 + baseUrl1

        # set the inputs based on the method inputs
        course1 = "&course1=" + Department + CourseNumber
        section1 = "&section1=" + Section
        term1 = "&term1=" + term

        # we set a variable called session1, I have always found it to equal B
        session1 = "&session1=B"

        pageText = self.session.get(
            baseUrl + course1 + section1 + term1 + session1).text

        bookList = []

        bookInfoList = pageText.split("<tbody>")[1].split(
            "</tbody>")[0].split("<tr>")[1:]

        for bookInfo in bookInfoList:

            infoList = bookInfo.split("<td")

            tempBook = {}

            # gets all the book info, adds nothing is something errors
            try:
                tempBook["author"] = infoList[1][1:-5]
                tempBook["title"] = infoList[2][1:-5]
                tempBook["required"] = infoList[3].split(">")[1][:-4]
                tempBook["course"] = infoList[4][1:-5]
                tempBook["isbn"] = infoList[5][1:-5]
                tempBook["new"] = float(infoList[6].split(">")[1][:-4].strip())
                tempBook["used"] = float(
                    infoList[7].split(">")[1][:-4].strip())
                tempBook["newRent"] = float(
                    infoList[8].split(">")[1][:-4].strip())
                tempBook["usedRent"] = float(
                    infoList[9].split(">")[1][:-4].strip())
                bookList.append(tempBook)
            except:
                pass

        return bookList

    # look up overall GPA
    def GPA(self):

        # set the url (broken up for line length)
        url0 = "https://isis-cs.prod.cu.edu/psc/csprod/UCB2/HRMS/c/"
        url1 = "SA_LEARNER_SERVICES.SSR_SSENRL_GRADE.GBL?"
        url2 = "ACAD_CAREER=UGRD&INSTITUTION=CUBLD&STRM=2151"
        baseUrl = url0 + url1 + url2

        # get the page text
        pageText = self.session.post(baseUrl).text

        # get the GPA
        splitText = pageText.split("PSEDITBOXLABEL")[-1].split(">")[1][:5]

        GPA = float(splitText)

        return GPA
