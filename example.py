#!/usr/bin/python
# coding=utf8
import getpass
import mycuinfo

# fix for python 3.x
try:
    raw_input = input
except NameError:
    pass

# define the username & password for the cuSession
user0 = raw_input("username: ")
pass0 = getpass.getpass("password: ")

# create the cuLog Session
cu_student = mycuinfo.CUSession(user0, pass0)

# if the loggin session is a valid one
if cu_student.valid:

    # example of how to get the books from CSCI 2700, Section 010 (Fall 2014)
    print(cu_student.books("CSCI", "2270", "010", term=2167))

    # example of how to get the info of the user
    print(cu_student.info())

    # example of how to get the classes of the user (Fall 2014)
    print(cu_student.classes())

    # example of how to get the GPA of the user
    print(cu_student.GPA())

else:
    print("Bad user. Check the username/password")
