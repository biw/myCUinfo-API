#myCUinfo-API#

##About##
This is a python wrapper for the [myCUinfo System](http://mycuinfo.colorado.edu) at the [University of Colorado Boulder](http://colorado.edu). It uses the [python requests library](http://python-requests.org) to scrape the data for any given student with valid login credentials. It currently is read only (you can't edit you classes with it) but I have plans on adding functionality to add/remove classes.

NOTE: I am not affiliated with the development of the myCUinfo system. This project has no indorsement by the University of Colorado.

##Getting Started##

First install the [Python Requests Library](http://docs.python-requests.org/en/latest/). To install Requests use the following command:
```bash
pip install requests
```
Then run the code with python 2.7

##Functions and Output##
The API currently has a few functions that scrape the info off the myCUinfo site. They all use methods on an initialized cuSessions logged in user. This way the convoluted login process is only handled once.

####cuSessions(username, password) (initializer)####
This is the overarching class of the myCUinfo API. It takes in a username & password of a myCUinfo user and returns a class object that is a logged in user.
```python
user = "example001"
password = "secret001"
loginUser = myCUinfo.cuSession(user, password)
```

####.info()####
This method returns the basic user information. We will format the output with json.
```python
userInfo = loginUser.info()
print json.dumps(userInfo, sort_keys=True, indent=4, separators=(',', ':'))
```

######Example Output:######
```python
{
    "Affiliation": "STUDENT",
    "ClassStanding": "UGRD",
    "College": "College Arts and Sciences",
    "EID": None, #Will include the Employee ID if the user has one
    "FirstName": "Chip",
    "LastName": "Buffalo",
    "Major": "Dance",
    "Minor": None, #Will return a Minor if the user has one
    "SID": 000000001 #Student ID
}
```

####.classes()####
The method returns the class information of the user for the optional given term. We will format the output with json.
```python
userClasses = loginUser.classes("Spring2015") #we can also call loginUser.classes() and it will default to the current semester
print json.dumps(userClasses, sort_keys=True, indent=4, separators=(',', ':'))
```

######Example Output:######
```python
[
    {
        "Building": "BESC",
        "ClassCP": "1010", #Primary Class Code. Ex: SPRT 1010
        "ClassCS": "001", #Secondary Class Code. Ex: Section 001
        "Credits": 4,
        "Days": "MWF",
        "Department": "SPRT",
        "EndTime": "10:50 AM",
        "Grade": None, #Will show a grade when looking at past semesters
        "Instructor": "Ralphie Buffalo",
        "Room": "180",
        "StartTime": "10:00 AM",
        "Status": "Enrolled", #Will show Waitlisted or Enrolled
        "Title": "Intro to Spirit (Lecture)"
    },
    ..., #Will list all classes but example output has been truncated to two classes
    {
        "Building": "ECCS",
        "ClassCP": "1010", #Primary Class Code. Ex: SPRT 1010
        "ClassCS": "010", #Secondary Class Code. Ex: Section 010
        "Credits": 0, #shows 0 credits because all credits go to Lecture class
        "Days": "W",
        "Department": "SPRT",
        "EndTime": "03:50 PM",
        "Grade": None,  #Will show a grade when looking at past semesters
        "Instructor": "Ralphie Buffalo",
        "Room": "112C",
        "StartTime": "03:00 PM",
        "Status": "Enrolled", #Will show Waitlisted or Enrolled
        "Title": "Intro to Spirit (Recitation)"
    },
]
```

####.books()####
The method returns the book information for a given class section for an optional given term. We will format the output with json.
```python
department = "SPRT"
courseNumber = "1010"
section = "010"
userBooks = loginUser.books(department, courseNumber, section, term="Spring2015") #term is optional, will default to current semester.
print json.dumps(userBooks, sort_keys=True, indent=4, separators=(',', ':'))
```

#####Example Output:######
```python
[
    {
        "Author": "BRYANT",
        "Course": "SPRT1010-010",
        "ISBN": "9780136102041",
        "New Price": 157.0,
        "New Rental Price": 102.25,
        "Required": true,
        "Title": "SCHOOL SPIRIT: A MASCOT'S PERSPECTIVE",
        "Used Price": 116.5,
        "Used Rental Price": 70.75
    }
]
```

####.GPA()####
The method returns the current GPA of student
```python
gpa = loginUser.GPA()
print "The current GPA is " + gpa
```

#####Example Output:######
```python
The current GPA is 3.991
```
