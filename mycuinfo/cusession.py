#!/usr/bin/python
# coding=utf8
import requests
import json
import html


# This script is downloaded when navigating to mycuinfo.colorado.edu.
# It contains a map of a bunch of urls. We can convert it to a dictionary
# And find the one students are interested in with the key iepprdUCB2 to
# hopefully avoid needing to update the url and having the API break all the time
def getURL(session):
    page_text = session.get('https://portal.prod.cu.edu/scripts/redirect.js').text
    ind0 = page_text.find('{')
    ind1 = page_text.find('}')
    url_map_string = page_text[ind0:ind1+1]
    lines = url_map_string.split('\n')
    good_lines = []
    for l in lines:
        if len(l)<20 and l.find('{')==-1 and l.find('}')==-1:
            continue
        good_lines.append(l)
    url_map_string = '\n'.join(good_lines)
    url_map = json.loads(url_map_string)
    return url_map['iepprdUCB2']

# Take in some html text and the names of the inputs we need
# Find the post url and the values for those inputs
def parseForm(text, names):
    form = text[text.find('<form')+len('<form'):text.find('</form>')]
    act0 = form.find('action="')+len('action="')
    act1 = form.find('"', act0+1)
    action = form[act0:act1]
    data = {}
    for n in names:
        input = form[form.find(n):]
        ind0 = input.find('value="')+len('value="')
        ind1 = input.find('"', ind0+1)
        data[n] = input[ind0:ind1]
    return html.unescape(action), data

class CUSession(requests.sessions.Session):

    # get past the weird javascript redirects that mycuinfo uses to login
    def __init__(self, username, password):

        session = requests.Session()
        url = getURL(session)
        # get the inital page, found url by disecting js code from
        # mycuinfo.colorado.edu
        init_page = session.get(url)
        init_text = init_page.text
        resume_url, resume_data = parseForm(init_text, ['SAMLRequest', 'RelayState'])
        resume_page = session.post(resume_url, data=resume_data)

        login_url, login_data = parseForm(resume_page.text, [])
        login_data['j_username'] = username
        login_data['j_password'] = password
        login_data['timezoneOffset'] = '0'
        login_data['_eventId_proceed'] = 'Log In'
        login_url = 'https://fedauth.colorado.edu' + login_url
        login_page1 = session.post(login_url, login_data)
        login_url2, login_data2 = parseForm(login_page1.text, ['SAMLResponse', 'RelayState'])
        login_page2 = session.post(login_url2, login_data2)

        last_url, last_data = parseForm(login_page2.text, ['SAMLResponse', 'RelayState'])
        last_page = session.post(last_url, last_data)

        # if the user/pass was bad, the url will not be correct
        if last_page.url != "https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/?tab=DEFAULT":
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

        # Each item will be formatted like <name>value</name> or <name>
        # Only items like the former will be added
        for item in splitText:
            name = item.split('<')[1].split('>')[0]
            value = item.split('>')[1].split('<')[0]
            if value != "":
                info[name] = value

        return info

    def classes(self, term="Spring 2019"):

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

            if len(courseSection) == 1:
                continue

            nameAndType = classInfo.split('<th')[1].split('>')[1].split('<')[0]
            nameAndType = nameAndType.split('&nbsp;')
            tempClass["name"] = nameAndType[0]
            tempClass["type"] = nameAndType[1][1:-1]
            classInfo = classInfo.split('</th>')[1]

            courseInfo = classInfo.split('<td>')[1].split('<br')[0]

            tempClass["department"] = courseInfo[0:4]
            courseInfo = courseInfo.split('-')
            tempClass["classCode"] = courseInfo[0][-4:]
            tempClass["section"] = courseInfo[1]
            classInfo = classInfo.split('</td>')[1:]

            dateAndTime = classInfo[0].split("meetingtime\"")[1][
                1:].split("</div>")[0].split(">")

            # Independent studys and probably other classes don't have a time listed
            try:
                tempClass["days"] = dateAndTime[0].split("<")[0][:-1]
                tempClass["startTime"] = dateAndTime[1].split("<")[0]
                tempClass["endTime"] = dateAndTime[3].split("<")[0]
            except:
                pass

            tempInstructor = {}

            # Some courses (mostly recitations) don't have an instructor listed
            try:
                instructorInfo = classInfo[1].split("meetingtime\"")[1][
                    1:].split("</div>")[0].split(">")

                instrutr = instructorInfo[0].split("&nbsp;")[0].split(" ")

                tempInstructor["firstName"] = instrutr[1]
                tempInstructor["lastName"] = instrutr[0]
            except:
                tempInstructor["firstName"] = "Staff"
                tempInstructor["lastName"] = ""

            tempClass["instructor"] = tempInstructor

            tempClass["credits"] = int(classInfo[3].split(">")[1])
            tempClass["status"] = classInfo[4].split(">")[1]
            tempClass["grade"] = classInfo[5].split(">")[1]

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
        # The available set of terms keeps changing, so it would be nice to calculate the available ones on the fly?
        # For now do it this way because I'm lazy
        if term == "Fall2015" or term == 2157:
            term = "2157"
        elif term == "Spring2015" or term == 2151:
            term = "2151"
        elif term == "Summer2015" or term == 2154:
            term = "2154"
        elif term=="Fall2016" or term == 2167:
            term = "2167"
        elif term == "Spring2016" or term == 2161:
            term = "2161"
        elif term == "Summer2016" or term == 2164:
            term = "2164"
        elif term=="Fall2017" or term == 2177:
            term = "2177"
        elif term == "Spring2017" or term == 2171:
            term = "2171"
        elif term == "Summer2017" or term == 2174:
            term = "2174"
        elif term=="Fall2018" or term == 2187:
            term = "2187"
        elif term == "Spring2018" or term == 2181:
            term = "2181"
        elif term == "Summer2018" or term == 2184:
            term = "2184"
        elif term=="Fall2019" or term == 2197:
            term = "2197"
        elif term == "Spring2019" or term == 2191:
            term = "2191"
        elif term == "Summer2019" or term == 2194:
            term = "2194"
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
                tempBook["author"] = infoList[1][1:-6]
                tempBook["title"] = infoList[2][1:-6]
                tempBook["required"] = infoList[3].split(">")[1][:-4]
                tempBook["course"] = infoList[4][1:-6].replace('\n', "")
                tempBook["isbn"] = infoList[5][1:-12]

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
