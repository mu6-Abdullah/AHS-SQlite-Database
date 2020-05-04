import sys #import necessary modules
import sqlite3 as sql
import datetime as dt
import getpass as gp

def main():
    print("This program was created by Adam Elamy and Muhammad Abdullah exclusively in Fall of 2019 for CMPUT 291 taught by Davood Rafiei.\n")
    file_name = sys.argv[1] #get command line argument
    conn = sql.connect('./'+ file_name)
    c = conn.cursor()
    c.execute(' PRAGMA foreign_keys=ON; ') #turn on foreign keys
    conn.commit()
    db = DB(c,conn) #run db
    conn.commit() #close db
    conn.close()

#the database class holds the individuals username and password
# sets up a login screen, validates credentials and provides access to their system
class DB:
    def __init__(self,c,conn): #TBD, ignore everything currently here as it will likely be changed
        #DB Attributes
        self.user = None
        self.password = None
        self.c = c
        self.conn = conn
        self.clearance = None
        self.cred = None
        self.city = None
        self.run()
    
    def run(self):
        loop = True #don't stop
        while loop:
            loop = False #flip flag
            success = self.print_login_screen() #check if user has logged in
            if success: #if they have
                self.city = self.cred.get_city()
                name = self.cred.get_name() #get their name,city and clearance
                self.clearance = self.cred.obtain_clearance()

                if self.clearance == 'a': #print welcome message
                    print("Welcome! You are currently logged on as Agent",name[0],name[1])
                else:
                    print("Welcome! You are currently logged on as Officer",name[0],name[1])
                print("\n")
                self.create_user() #create user
            self.clear_all() #otherwise or once that process is done, clear instance attributes for new run
            user_input = input("Would you like to do more today? '[y/Y]/[anything else to end it]' > ").lower() #check if they are done
            if user_input == 'y': #if yes, keep going
                print()
                loop = True
                
            else: #otherwise end it
                loop = False
                print("Thank you for your buisness. Good day!")
            
    def print_login_screen(self):
        done = False    #bool flag    
        while not done:
            print("Enter a valid username and password or 'q/Q',in either sections, to quit.") #print info
            self.user = input("Username: ") #prompts
            self.password = gp.getpass() 
            if self.user.lower() == 'q' or self.password.lower() == 'q': #check if user quit
                return False
            else: #otherwise validate credentials
                if self.validate_credentials():
                    return True
                else: #or tell them to print valid credentials
                    print("Please enter valid credentials.\n")
               
    def validate_credentials(self):
        self.cred = credential(self.user,self.password,self.c,self.conn) #create credential object
        if self.cred.validate() and self.cred.authenticate(): #validate and authenticate credentials
            return True
        return False
    
    def clear_all(self): #clear all the instance attributes for the next iteration of DB
        self.user = None
        self.password = None
        self.city = None
        self.clearance = None
        self.cred = None
    
    def create_user(self): #create agent or officer object depending on clearance
        if self.clearance == 'a': 
            agent = Agent(self.c,self.user,self.password,self.conn,self.city)
        elif self.clearance == 'o':
            officer = Officer(self.c,self.user,self.password,self.conn) 

# the credentials class validates the inidividuals username and password
class credential:
    
    def __init__(self,user,password,c,conn): #create instance attributes
        self.password = password
        self.user = user
        self.clearance = None
        self.conn = conn
        self.fname = None
        self.lname = None
        self.city = None
        self.c = c
    
    def validate(self): #check if credential is alphanumeric (helps prevent injection attacks)
        #character check
        return (self.user.isalnum() and self.password.isalnum())
    
    def authenticate(self): #check if credential is in the database
        #database check
        self.c.execute("SELECT utype,fname,lname,city FROM users WHERE uid = :uid collate NOCASE AND pwd = :pwd" ,{"uid":self.user,"pwd":self.password})
        try:
            value = self.c.fetchone()
            self.clearance = value[0]
            self.fname = value[1]
            self.lname = value[2]
            self.city = value[3]
            return True
        except TypeError:
            print("The username or password you entered is invalid.")
            return False
       
        return False
    
    def obtain_clearance(self): #return the clearance level
        #admin level
        return self.clearance
    
    def get_name(self): #return their name
        return [self.fname,self.lname]
    
    def get_city(self): #return their city
        return self.city

class Agent: #provides agent functionalities
    
    def __init__(self,c,user,password,conn,city): #initializes instance attributes
        self.conn = conn
        self.list1 = [] #empty list for get input
        self.user_headers = ["birth date (YYYY-MM-DD)", "birth place", "address","phone number"] #headers for get input when creating info list for a person
        self.username = user
        self.password = password
        self.c = c
        self.city = city
        self.a_run() #run the run method
    
    def a_run(self): #will run the interface and call the different functions
        done = False #set bool flag
        while not done: #loop
            user_input = self.a_create_interface() #create the interface and get user input from it
            if user_input == 'q': #if user quits end the loop
                done = True
            elif user_input == 'b': #otherwise match the symbol to the correct method
                self.register_birth()
            elif user_input == 'm':
                self.register_marriage()
            elif user_input == 'v':
                self.renew_registration()
            elif user_input == 's':
                self.process_bill()
            elif user_input == 'p':
                self.process_payment()
            elif user_input == "a":
                self.get_abstract()

    def register_birth(self): #registers a birth in births and persons
        birth_info = [] #to hold birth details
        birth_id = ID(0,self.c,self.conn) #create birth id
        birth_info.append(birth_id.create_id())
        birth_info_titles = ["child's first name","child's last name","gender","father's first name","father's last name","mother's first name","mother's last name","child's birth date (YYYY-MM-DD)"]
        birth_info = get_input(birth_info,birth_info_titles) #get user input and add to list
        c_birth_day = birth_info.pop()
        birth_info.insert(3,dt.date.today()) #insert regdate and city in appropriate place
        birth_info.insert(4,self.city)

        
        try: #ensure a name is provided for the child, mother and father
            assert (birth_info[1] != '' and birth_info[2] != ''),"Error, no child's name"
            assert (birth_info[5] == '' or (len(birth_info[5]) == 1 and birth_info[5].lower() in ['m','f'])),"Error, gender is invalid"
            assert (birth_info[6] != '' and birth_info[7] != ''),"Error, no father's name"
            assert (birth_info[8] != '' and birth_info[9] != ''),"Error, no mother's name"
            
        except AssertionError as e:
            print(e)
            print()
            return
       
        self.check_person_exists([birth_info[6],birth_info[7]]) #inserts parents if they do not exist
        self.check_person_exists([birth_info[8],birth_info[9]])
        #null_maker(birth_info) #makes None into (None,) tuple for SQLite standards
        
        self.c.execute("SELECT address,phone FROM persons WHERE fname = :fname collate NOCASE AND lname = :lname collate NOCASE GROUP BY address,phone;",{"fname":birth_info[8],"lname":birth_info[9]})
        row = self.c.fetchone() #gets mom's address and phone so that birth can be registered in persons
        person_birthed_info = birth_info[1:3] #gets info from births for persons
        person_birthed_info.append(c_birth_day)
        person_birthed_info.append(birth_info[4])
        person_birthed_info.append(row[0]) #add the phone and address
        
        person_birthed_info.append(row[1])
        
        self.create_person(values = person_birthed_info) #create a person 
        try: #get mom and dads names as inputted in database i.e. exchange case insensitive for case sensitive data
            self.c.execute("SELECT fname,lname FROM persons WHERE fname = ? collate NOCASE and lname = ? collate Nocase;",(birth_info[6],birth_info[7]))
            row = self.c.fetchone()
            self.c.execute("SELECT fname,lname FROM persons WHERE fname = ? collate NOCASE and lname = ? collate Nocase;",(birth_info[8],birth_info[9]))
            row1 = self.c.fetchone()
            self.c.execute("INSERT INTO births VALUES (?,?,?,?,?,?,?,?,?,?);",(birth_info[0],birth_info[1],birth_info[2],birth_info[3],birth_info[4],birth_info[5],row[0],row[1],row1[0],row1[1]))
        except sql.IntegrityError as e:
            print("The tuple you were trying to insert fails integrity contraints.\n")
        self.conn.commit() #insert birth into births
   
    def register_marriage(self): #registers a marriage
        marriage_info = [] #for marriage
        marriage_id = ID(1,self.c,self.conn) 
        marriage_info.append(marriage_id.create_id()) #create marriage ID
        marriage_info.append(dt.date.today()) #get marriage date and place
        marriage_info.append(self.city)
        marriage_info_header = ["partner one's first name","partner one's last name","partner two's first name","partner two's last name"]
        get_input(marriage_info,marriage_info_header) #get rest of info
        
        try: #check that both partners have names
            assert (marriage_info[3] != '' and marriage_info[4] != '')
            assert (marriage_info[5] != '' and marriage_info[6] != '')
        except AssertionError:
            print("Both partners must have names!\n")
            return
            
        self.check_person_exists([marriage_info[3],marriage_info[4]]) #insert p1 and p2
        self.check_person_exists([marriage_info[5],marriage_info[6]])
        try: #get partner 1 and 2 as case sensitive from case insensitive input
            self.c.execute("SELECT fname,lname FROM persons WHERE fname = ? collate NOCASE and lname = ? collate Nocase;",(marriage_info[3],marriage_info[4]))
            row = self.c.fetchone()
            self.c.execute("SELECT fname,lname FROM persons WHERE fname = ? collate NOCASE and lname = ? collate Nocase;",(marriage_info[5],marriage_info[6]))
            row1 = self.c.fetchone()
            self.c.execute("INSERT INTO marriages VALUES (?, ?, ?, ?, ?, ?, ?);",(marriage_info[0],marriage_info[1],marriage_info[2],row[0],row[1],row1[0],row1[1]))
        except sql.IntegrityError:
            print("The tuple you were trying to insert fails integrity contraints.")
        self.conn.commit()  #create marriage

    def renew_registration(self): #renew reg.
        date_today = dt.date.today() #get current date
        regno = input("Enter an existing registration number: ") #get regno
        self.c.execute("SELECT expiry,count(regno) FROM registrations WHERE regno = ? GROUP BY expiry;",(regno,))
        row = self.c.fetchone()
        try: #check if the registration existed
            date_returned = row[0]
        except TypeError:
            print("That registration did not exist!\n")
            return

        fixed_date_returned = dt.datetime.strptime(date_returned, "%Y-%m-%d").date() #turn expiry date into date object
        count = row[1] #get expiry date and check if regno is valid

        if count: #if regno exists
            if fixed_date_returned <= date_today: #and the expiry date is today or has passed
                current_date = date_today
                current_date = change_date(current_date,1) #find the date in a year
                self.c.execute("UPDATE registrations SET expiry = ? ,regdate = ? WHERE regno = ?",(current_date,date_today,regno))
                #update the reg and expiry dates
            elif fixed_date_returned > date_today: #if it has not yet expired
                expiry_date = fixed_date_returned
                expiry_date = change_date(expiry_date,1) #add a year to expiry date
                self.c.execute("UPDATE registrations SET expiry = ?, regdate = ? WHERE regno = ?",(expiry_date,date_today,regno))
                #update expiry and reg date
            self.conn.commit()
        else:
            print("The registration number entered was invalid.") #otherwise print that the value was wrong
    
    def process_bill(self): #q4
         # things the bill of sale will change/update
        # give a person a new car
        # Create a new registration  
        # find an existing car to sell by getting the vin
        current_date = dt.date.today() #get the current date
        #bill_info[vin,current_owner, new_owner, new plate number]
        bill_info = [] #create an empty list to append all the information required
        new_regno = ID(3,self.c,self.conn) #create a new regno (IDTYPE)
        new_regno = new_regno.create_id()
 
        
        self.c.execute("Select vin from registrations;") #retrieve all vins and append into a list
        vin_list = self.c.fetchall()
        vin_list = untupler(vin_list) #removes everything except the beginning bits to compare
        #ORDER of bill_info
        #0: new_regno, #1: current_date, #2: date + year, #3: vin-number, #4: new-owners fname, #5: new-owners lname, #6: current-owners fname,
        #7: current-owners lname, #8 plate number
        bill_info.append(new_regno)
        bill_info.append(current_date)
        next_year = change_date(current_date,1)
        bill_info.append(next_year)
        bill_info_titles =["existing vin number", "new owner's first name ","new owner's last name "," current owner's first name","current owner's last name" ,"new plate number"]
        get_info = get_input(bill_info,bill_info_titles) #fill the bill_info with the get_input func
        vin = bill_info[3] #label the vin
        #CHECK IF VALID VIN
 
        if vin not in vin_list: #check if the vin is a valid vin in the database
            print("Invalid Vin!\n")
            return
        if not self.check_person_exists([bill_info[4],bill_info[5]],sale = True): #check if new owner in database
            print("The new owner does not exist in the database currently!")
            return

        self.c.execute("SELECT lname FROM registrations WHERE vin = ? collate NOCASE ORDER BY regdate;",(bill_info[3],))
        most_recent_owner = self.c.fetchone() #get the most recent owner
        
        if bill_info[7] == most_recent_owner[0]:# compare the the bill_info[7] 
            print("The purchase is valid!")
        else:
            print("The previous owner listed is not the most recent owner of the car")
        #UPDATE THE PLATE WITH REGISTRATION
        self.c.execute(" UPDATE registrations SET expiry = ? WHERE vin = ? AND fname = ? collate NOCASE AND lname = ? collate NOCASE;",(bill_info[2],bill_info[3],bill_info[6],bill_info[7]))
        self.conn.commit()
        #REGNO, #REGDATE, EXPIRY, PLATE, VIN, FNAME, LNAME
        try:
            self.c.execute("INSERT INTO registrations VALUES (?,?,?,?,?,?,?);",(bill_info[0],bill_info[1],bill_info[2], bill_info[8],bill_info[3], bill_info[4],bill_info[5]))
        except sql.IntegrityError: #try to insert the the values in bill_info to update the table
            print("The tuple you were trying to insert fails integrity contraints.")
        self.conn.commit()
        # same vin but unique regno
    
    def process_payment(self): #q5
        tno = input("Enter an existing ticket number: ") #enter a tno
        self.c.execute("SELECT t.tno,t.fine,(t.fine - SUM(p.amount)) FROM tickets t LEFT JOIN payments p USING(tno) WHERE t.tno = ? GROUP BY t.tno,t.fine;",(tno,))
        row = self.c.fetchone() #get the fine amount
        try:
            if row[2] == None: #if no payments have been made 
                fine = row[1]
            else: #if payments have been made
                fine = row[2]
        except TypeError: #if typeError then it does not exist
            print("That ticket number did not exist!\n")
            return
        
        payment = int(input("Enter a valid payment amount: ")) #get a payment amount
        
        deduction = fine - payment #check if it is more than the remaing balance
        if deduction < 0: #if so tell the user such
            if fine == 0:
                print("The ticket is already paid off!")
            else:
                print("You are paying too much! The remaining balance is only %i" % (fine))
        else: #otherwise add the payment
            try:
                self.c.execute("INSERT INTO payments VALUES (?, ?, ?);",(tno,dt.date.today(),payment))
            except sql.IntegrityError:
                print("The tuple you were trying to insert fails integrity contraints.")
            self.conn.commit()
        print("")

    
    def get_abstract(self): #q6
        values = [] #empty list for getinput
        two_info = [] #list for info between 2 years
        header_list = ["first name","last name"] #list of info we need from user
        values = get_input(values,header_list) #get first and last name

        self.c.execute('''SELECT p.fname,p.lname,COALESCE(COUNT(t.tno),0),COALESCE(COUNT(d.ddate),0),COALESCE(SUM(d.points),0) FROM persons p
                          LEFT OUTER JOIN registrations r USING (fname,lname) LEFT OUTER JOIN tickets t USING(regno)
                          LEFT OUTER JOIN demeritNotices d USING (fname,lname) WHERE p.fname = ? collate NOCASE AND p.lname = ? collate NOCASE
                          GROUP BY p.fname,p.lname;''',(values[0],values[1]))
        all_row = self.c.fetchone() #get all the info over all time
        try: #check if the person exists in the db
            value = all_row[0]
        except TypeError:
            print("That person does not exist!\n")
            return
            #if the person exists, get their demerit info and ticket info over the past 2 years
        self.c.execute('''SELECT p.fname,p.lname,COALESCE(COUNT(d.ddate),0),COALESCE(SUM(d.points),0) FROM persons p
                          LEFT OUTER JOIN registrations r USING (fname,lname) LEFT OUTER JOIN demeritNotices d
                          USING (fname,lname) WHERE d.ddate >= date('now','-2 years') AND p.fname = ?  collate NOCASE AND p.lname = ? collate NOCASE GROUP BY p.fname,p.lname;''',(values[0],values[1]))
        two_row = self.c.fetchone()

        self.c.execute('''SELECT p.fname,p.lname,COALESCE(COUNT(t.tno),0) FROM persons p LEFT OUTER JOIN registrations r
                          USING (fname,lname) LEFT OUTER JOIN tickets t USING(regno) 
                           WHERE t.vdate >= date('now','-2 years') AND p.fname = ? collate NOCASE AND p.lname = ?  collate NOCASE GROUP BY p.fname,p.lname;''',(values[0],values[1]))
        two_row1 = self.c.fetchone()
        try: #add the info into the list, if it is None and causes a typeError add 0
            two_info.append(two_row1[2])
        except TypeError:
            two_info.append(0)
        try:
            two_info.append(two_row[2])
            two_info.append(two_row[3])
        except TypeError:
            two_info.append(0)
            two_info.append(0)
        
        headers = ["Number of tickets","Number of demerit notices","Total number of demerit points"] #header list of info we will print
        print("Driver's abstract for",all_row[0],all_row[1]) #inform user of driver name
        print("")
        for x in range(len(headers)): #iterate over headers and provide info for all time and within the last 2 years
            print(headers[x])
            print("All time:",all_row[x+2])
            print("Within two years:",two_info[x])
            print()

        
        user_input = input("Enter 'y/Y' if you would like to see all the tickets or anything else if not: ")
        if user_input.lower() == 'y':
            if all_row[2] != 0: #if the user has tickets
                self.c.execute('''SELECT r.regno,v.make,v.model,t.tno,t.vdate,t.violation,t.fine FROM registrations r, tickets t, vehicles v 
                 WHERE t.regno = r.regno AND v.vin = r.vin AND r.fname = ? collate NOCASE AND r.lname = ? collate NOCASE ORDER BY t.vdate DESC''',(values[0],values[1]))
                row = self.c.fetchall() #get all the tickets

                print("Ticket summary for",values[0],values[1]) #inform user of drive name
                print("The information provided is the regno,make,model,tno,vdate,violation and fine amount respectively\n")
                #provide format of info

                for x in range(len(row)): #iterate over info and print
                    if x % 5 == 0 and x != 0: #once we hit 5
                        user_input = input("Enter 'y/Y' if you would like to see all the tickets or anything else if not: ") #check with user if they want to see more
                        if user_input.lower() != 'y': #if the user does not enter y, then break
                            break
                    print(','.join(map(str,row[x]))) #print the tuples as strings, turn non-strings into strings
                    
                    print("\n")
                    
                    
            else: #if the user has no tickets, inform the user of such
                print(values[0],values[1],"has no tickets")
                

    def a_create_interface(self): #create interface for agents
        codes = ["b","m","v","s","p","a","q"] # all the different codes to be printed
        meanings = ["Register a birth","Register a marriage","Renew a vehicle registration","Process a bill of sale","Process a payment","Get a driver abstract","Quit"]
        #meanings of the codes to be printed along side the codes
        print("Agents can do the following:") #header
        for x in range(len(codes)): #print out the codes and their meaning
            print(meanings[x]+":",codes[x])
        user_input = ""
        while user_input.lower() not in codes: #prompt for a code until a valid code is entered
            user_input = input("Please enter a valid code: ")
        return user_input.lower()
    
    def create_person(self,name = [],values = []): #create person i.e. their list to be inserted
        if not len(values): #if list is not already provided i.e. the list is from a birth
            self.list1.append(name[0]) #add the name
            self.list1.append(name[1])
            self.list1.append(get_input(self.list1,self.user_headers,name)) #create the list
        if len(values): #if list provided
            self.insert_person(values) #insert it
        else: #otherwise, insert the instance attribute list just created
            self.insert_person() 
        self.clear_list() #empty list for next time
    
    def insert_person(self,values = []): #insert person 
        if len(values): #insert person from either availibe list, values is used if it is from births otherwise self.list1 is used
            try:
                self.c.execute("INSERT INTO persons  VALUES (?,?,?,?,?,?);",(values[0],values[1],values[2],values[3],values[4],values[5]))
            except sql.IntegrityError:
                print("The tuple you are attempting to insert fails integrity constraints.")
            else:
                self.conn.commit()

        else:
            self.list1.pop()
            self.c.execute("INSERT INTO persons  VALUES (?,?,?,?,?,?);",(self.list1[0],self.list1[1],self.list1[2],self.list1[3],self.list1[4],self.list1[5]))
            self.conn.commit()
    
    def clear_list(self):
        self.list1 = [] #clear list
    
    def check_person_exists(self,name,sale = None):#check if person exists in database already
        self.c.execute("SELECT COUNT(fname) FROM persons WHERE fname = :fname collate NOCASE AND lname = :lname collate NOCASE;",{"fname":name[0],"lname":name[1]}) #count their occurence
        row = self.c.fetchone() #if they don't occur once, then create them
        if sale == None:
            if row[0] != 1:
                self.create_person([name[0],name[1]])
        else:
            if row[0] == 1:
                return True
            return False

class Officer:
    # officer class, displays all functions that the officer can perform
    def __init__(self,c,user,password,conn):
        self.c = c #instance attributes for the class
        self.conn = conn
        self.user = user
        self.password = password
        self.o_run()
    def o_run(self):
        done = False #bool flag
        while not done: 
            user_input = self.o_create_interface() #get input
            if user_input == 'q': #when to quit
                done = True
            elif user_input == 't': #otherwise call the methods and then run another loop
                self.issue_ticket()
            elif user_input == 'o':
                self.find_owner()

    def issue_ticket(self):
        entered_regno = input("Enter an existing registration number: ") #prompt for regno
        self.c.execute("SELECT r.fname,r.lname,v.make,v.model,v.year,v.color FROM registrations r,vehicles v WHERE r.regno = ? AND v.vin = r.vin;",(entered_regno,))
        row = self.c.fetchone() #get info for regno
        try:
            print("The following details are for regno",entered_regno) #try to print out the details line by line
            headers = ["First name","Last name","Car make","Car model","Car fabrication year","Car color"]
            for x in range(len(row)):
                print(headers[x]+":",row[x])
        except TypeError: #if it gives a type error then we are subscripting a None and then regno did not exist
            print("That registration number did not exist!\n")
            return
        else: #if the try worked
            user_input = input("Enter 'y/Y' if you would like to issue a ticket or anything else if not: ") #prompt user to continue
            if user_input.lower() == 'y': #if user wishes to continue
                values = []
                header_list = ["violation date (YYYY-MM-DD)","violation text","fine amount"]
                values = get_input(values,header_list) #get input
                try:
                    values[2] = int(values[2]) #turn fine amount into an int
                except ValueError:
                    values[2] = 0
                
                if values[0] == '': #if user left date empty set it
                    values[0] = dt.date.today()
                
                ticket_ID = ID(2,self.c,self.conn) #make a ticket id
                new_tno = ticket_ID.create_id() #add a ticket
                try:
                    self.c.execute("INSERT INTO tickets VALUES (?,?,?,?,?);",(new_tno,entered_regno,values[2],values[1],values[0]))
                except sql.IntegrityError:
                    print("The tuple you were trying to insert fails integrity contraints.")
                self.conn.commit()
        finally:
            print("\n")
    def find_owner(self):
        
        #Find the owner of a car by providing one or more of the make, model, year, color, and plate. The system should return all matches
        # let the user select one
        #When matches <4, or when a car is selected from a list shown earlier
        #make model year, color, and plate and regdate, expiry date, will be shown
        # about the person listed in the latest registration record
        given_inputs = []
        car_input_headers = [ "make ", "model ", "year ", "plate "]
        given_inputs = get_input(given_inputs,car_input_headers)
    
        output = []
        if car_input_headers[0]:
            #get all the info from the tables with the following conditions
            self.c.execute("select * from registrations natural join vehicles where make = ? collate NOCASE",(given_inputs[0],))
            rows = self.c.fetchall()
            for i in rows:
                output.append(i)
        if car_input_headers[1]:
            self.c.execute("select * from registrations natural join vehicles where model = ? collate NOCASE",(given_inputs[1],))
            rows1 = self.c.fetchall()
            for i1 in rows1:
                output.append(i1)
        if car_input_headers[2]:
            self.c.execute("select * from registrations natural join vehicles where year = ? ",(given_inputs[2],))
            rows2 = self.c.fetchall()
            for i2 in rows2:
                output.append(i2)
        if car_input_headers[3]:
            self.c.execute("select * from registrations natural join vehicles where plate = ? collate NOCASE",(given_inputs[3],))
            rows3 = self.c.fetchall()
            for i3 in rows3:
                output.append(i3)
        f_list = rows + rows1 + rows2 + rows3
       
        d = {} #create empty dictionary
        for x in range(len(f_list)): #iterate over list of tuples
            value = dt.datetime.strptime(f_list[x][1], "%Y-%m-%d").date() #set value of date
            if f_list[x][0] not in d: #check if vin in dictionary
                
                d[f_list[x][0]] =  ([value] + [i for i in f_list[x][2:len(f_list[x])]]) #if not assign vin (key) to rest of list
            else: #otherwise if vin is in the dictionary
                
                if d[f_list[x][0]][0] < value: #compare values of dates
                    d[f_list[x][0]] =  ([value] + [i for i in f_list[x][2:len(f_list[x])]]) #if value is smalled, swap lists
        final_output = [] #final output list
        for k,v in d.items():   #iterate over dictionary and store items in list
            final_output.append([k]+v)
            

        if len(final_output) < 4:
            for i in range(len(final_output)):
                print("The information above consists of the vehicle's make, model, year, color, plate, latest regdate, expiry and the name of person listed in record")
                print(str(i)+")",final_output[i][7], final_output[i][8], final_output[i][9], final_output[i][10], final_output[i][3], final_output[i][2],final_output[i][5]+' '+final_output[i][6])
                #make, model, year, color, plate, latest registration date, expiry, name of person listed in record
        else: #len(final_output>4)
            for i in range(len(final_output)):
                print("The information above consists of the vehicle's make, model, year, color and plate")
                print(str(i)+")",final_output[i][7], final_output[i][8], final_output[i][9], final_output[i][10], final_output[i][3])
                #print all the values required when output greater than 4
                #make, model, year, color, plate
            
            valid_input = False
            while (valid_input == False):
                try:
                    select = int(input("Please make a selection by inputting one of the above digits that corresponds to each vehicle: "))
                    assert select >=0, "Error out of range "
                    assert select <= len(final_output)-1, "Error out of range "
                except:
                    print("Please make sure the value inputted is a number in the given range ")
                else:
                    print("You have selected vehicle number:",select)
                    print(final_output[select][7], final_output[select][8], final_output[select][9], final_output[select][10], final_output[select][3], final_output[select][2],final_output[select][5]+' '+final_output[select][6])
                    valid_input = True
 
 
  
    def o_create_interface(self):
        codes = ["t","o","q"] #list of possible codes
        meanings = ["Issue a ticket","Find a car owner","Quit"] #list of code meanings
        print("Officers can do the following:") #initial header
        for x in range(len(codes)): #iterate through codes
            print(meanings[x]+":",codes[x])
        user_input = ""
        while user_input.lower() not in codes: #invalid input, re-prompt
            user_input = input("Please enter a valid code: ")
        return user_input.lower() #return lowercase of user input

class ID:
    # ID CLASS, different registrations require inidividual identification
    # this validates all the insertions that are going to be put into the database 
    def __init__(self,id_type,c,conn):
        #ID type, the connection to the database, list of values with all IDs
        self.conn = conn
        self.type = id_type
        self.values = []
        self.c = c
        self.get_current_ids()
        self.values = untupler(self.values)
    
    def get_current_ids(self):
        # helper function that specifies what to grab
        if self.type == 0:
            self.get_birth_ids()
        elif self.type == 1:
            self.get_marriage_ids()
        elif self.type == 2:
            self.get_ticket_ids()
        elif self.type == 3:
            self.get_regno_ids()
    
    def get_birth_ids(self): #grab different ids based on specific id
        self.c.execute("Select regno FROM births;")
        self.values = self.c.fetchall()
    
    def get_marriage_ids(self): #get all the marriage reg numbers
        self.c.execute("Select regno FROM marriages;")
        self.values = self.c.fetchall()
    
    def get_ticket_ids(self): #get all the tno from tickets
        self.c.execute("Select tno FROM tickets;")
        self.values = self.c.fetchall()

    def get_regno_ids(self): #get all the ids from registrations
        self.c.execute("Select regno FROM registrations;")
        self.values = self.c.fetchall()
    def create_id(self): #take the max and add one to make a unique id
        try:
            return max(self.values) + 1
        except ValueError: #if list is empty just add 1
            return 1

def get_input(empty_list,header_list,name = []):
    # gets a list of headers and an empty list, and creates a full list
    # asks for individual input and grabs the values to update in the database
    for x in range(len(header_list)): #iterate over header list
        if len(name): #when getting info for a certain user, print users name
            print(name[0],name[1],"is not in the database.")
        user_input = input("Please enter the " + header_list[x].lower()+" or press enter for None: ") #prompt user
        empty_list.append(user_input.strip()) #strip input
    return empty_list #return list
    

def null_maker(values): #turns pythonic nulls into null tuples so they can be inserted into sqlite properly
    for x in range(len(values)): #loop over values
        if values[x] == None or values[x] == '': #if values are none
            values[x] = (None,) #replace with the None tuple


def change_date(user_date,y): #add one year to the date
    try: #works in most cases
        return user_date.replace(year = user_date.year + y) #replace date with date + certain amount of years
    except ValueError: #occurs if that date does not exist in the following calendar year i.e. Feb 29, changes it to March 1
        return user_date + (dt.date(user_date.year + y, 1, 1) - dt.date(user_date.year, 1, 1))  #increment day and year
        #https://stackoverflow.com/questions/15741618/add-one-year-in-current-date-python

def untupler(tupled_list): #takes list of length one tuples and turns into list
    new_list = [] #create list
    for x in range(len(tupled_list)): #iterate over tuples
        for y in range(len(tupled_list[x])):
            new_list.append(tupled_list[x][y]) #append first item
    return new_list #return list

main()