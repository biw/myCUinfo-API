myCUinfo-API
------------

A python wrapper for the [myCUinfo System](http://mycuinfo.colorado.edu) at the [University of Colorado Boulder](http://colorado.edu).

NOTE: I am not affiliated with the development of the myCUinfo system. This project has no indorsement by the University of Colorado.

Getting Started
---------------
First install the [Python Requests Library](http://docs.python-requests.org/en/latest/). To install Requests use the following command:
```bash
pip install requests
```
Then run the code with python 2.7 or 3.x

##Functions and Output##
The API currently has a few functions that scrape the info off the myCUinfo site. They all use methods on an initialized cuSessions logged in user. This way the convoluted login process is only handled once.

####cuSession(username, password) (initializer)####
This is the initializer for the myCUinfo API class. It takes in a username & password of a myCUinfo user and returns a class object that is a logged in user.
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
    "affiliation": "STUDENT",
    "classStanding": "UGRD",
    "college": "College Arts and Sciences",
    "eid": None, #Will include the Employee ID if the user has one
    "firstName": "Chip",
    "lastName": "Buffalo",
    "major": "Dance",
    "minor": None, #Will return a Minor if the user has one
    "sid": 000000001 #Student ID
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
        "classCode": "1010", #Primary Class Code. Ex: SPRT 1010
        "section": "001", #Secondary Class Code. Ex: Section 001
        "credits": 4,
        "days": "MWF",
        "department": "SPRT",
        "endTime": "10:50 AM",
        "grade": "A", #will not show for current semester
        "instructor": "Ralphie Buffalo",
        "startTime": "10:00 AM",
        "status": "Enrolled", #Will show Waitlisted or Enrolled
        "name": "Intro to Spirit (Lecture)"
    },
    ..., #Will list all classes but example output has been truncated to two classes
    {
        "classCode": "1010", #Primary Class Code. Ex: SPRT 1010
        "section": "010", #Secondary Class Code. Ex: Section 010
        "credits": 0, #shows 0 credits because all credits go to Lecture class
        "days": "W",
        "department": "SPRT",
        "endTime": "03:50 PM",
        "grade": "A-", #will not show for current semester
        "instructor": "Ralphie Buffalo",
        "startTime": "03:00 PM",
        "status": "Enrolled", #Will show Waitlisted or Enrolled
        "name": "Intro to Spirit (Recitation)"
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
        "author": "BRYANT",
        "course": "SPRT1010-010",
        "isbn": "9780136102041",
        "new": 157.0,
        "newRent": 102.25,
        "required": true,
        "title": "SCHOOL SPIRIT: A MASCOT'S PERSPECTIVE",
        "used": 116.5,
        "usedRent": 70.75
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

To Do
-----
- [X] Python 2.7+ & 3.x support
- [ ] Create read-only of class listings
- [ ] Make API do writes

Contribution
------------
I welcome all kinds of contribution.

If you have any problem using the myCUinfo-API, please file an issue in Issues.

If you'd like to contribute on source, please upload a pull request in Pull Requests.

License
-------
MIT

