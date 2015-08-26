import myCUinfo
import getpass

# define the username & password for the cuSession
user0 = input("username: ")
pass0 = getpass.getpass("password: ")

# create the cuLog Session
cuLog = myCUinfo.cuSession(user0, pass0)


# if the loggin session is a valid one
if cuLog.valid:

    # example of how to get the books from CSCI 2700, Section 010 (Fall 2014)
    print(cuLog.books("CSCI", "2270", "010"))

    # example of how to get the info of the user
    print(cuLog.info())

    # example of how to get the classes of the user (Fall 2014)
    print(cuLog.classes())

    # example of how to get the GPA of the user
    print(cuLog.GPA())

else:
    print("Bad user. Check the username/password")
