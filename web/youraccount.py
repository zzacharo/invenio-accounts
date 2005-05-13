## $Id$
##
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""CDSware ACCOUNT HANDLING"""

__lastupdated__ = """$Date$"""

import sys
from cdsware import webuser
from cdsware.config import weburl,cdsname,cdslang,supportemail
from cdsware.webpage import page
from cdsware import webaccount
from cdsware import webbasket
from cdsware import webalert
from cdsware import webuser
from cdsware.access_control_config import *
from mod_python import apache  
from cdsware.access_control_config import CFG_ACCESS_CONTROL_LEVEL_SITE, cfg_webaccess_warning_msgs, CFG_EXTERNAL_AUTHENTICATION
import smtplib

def edit(req, ln=cdslang):
    uid = webuser.getUid(req)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return webuser.page_not_authorized(req, "../youraccount.py/set")

    data = webuser.getDataUid(req,uid)
    email = data[0]
    passw = data[1]
    return page(title="Your Settings",
                body=webaccount.perform_set(email,passw),
                navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">Your Account</a>""" % (weburl, ln),
                description="CDS Personalize, Your Settings",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def change(req,email=None,password=None,password2=None,login_method="",ln=cdslang):
    uid = webuser.getUid(req)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return webuser.page_not_authorized(req, "../youraccount.py/change")

    if login_method and CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS < 4:
        title = "Settings edited"
        act = "display"
        linkname = "Show account"
        prefs = webuser.get_user_preferences(uid)
        prefs['login_method'] = login_method
        webuser.set_user_preferences(uid, prefs)
        mess = "Login method successfully selected."
    elif login_method and CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 4:
        return webuser.page_not_authorized(req, "../youraccount.py/change")
    elif email:
        uid2 = webuser.emailUnique(email)
        if (CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 2 or (CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS <= 1 and webuser.checkemail(email))) and uid2 != -1 and (uid2 == uid or uid2 == 0) and password == password2:
            if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS < 3:
                change = webuser.updateDataUser(req,uid,email,password)
            else:
                return webuser.page_not_authorized(req, "../youraccount.py/change")
            if change and CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 2:
                mess = "Password successfully edited."
            elif change:
                mess = "Settings successfully edited."
       	    act = "display"
            linkname = "Show account"
            title = "Settings edited"
        elif uid2 == -1 or uid2 != uid and not uid2 == 0:
            mess = "The email address is already in use, please try again."
       	    act = "edit"
            linkname = "Edit settings"
            title = "Editing settings failed"
        elif not webuser.checkemail(email):
            mess = "The email address is not valid, please try again."
       	    act = "edit"
            linkname = "Edit settings"
            title = "Editing settings failed"
        elif password != password2:
            mess = "The passwords do not match, please try again."
       	    act = "edit"
            linkname = "Edit settings"
            title = "Editing settings failed"
    else:
        mess = "Could not update settings."
       	act = "edit"
        linkname = "Edit settings"
        title = "Editing settings failed"
            
    return page(title=title,
 	        body=webaccount.perform_back(mess,act, linkname),
                navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">Your Account</a>""" % (weburl, ln),
                description="CDS Personalize, Main page",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def lost(req, ln=cdslang):
    uid = webuser.getUid(req)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return webuser.page_not_authorized(req, "../youraccount.py/lost")

    return page(title="Lost your password?",
                body=webaccount.perform_lost(),
                navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">Your Account</a>""" % (weburl, ln),
                description="CDS Personalize, Main page",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def display(req, ln=cdslang):
    uid =  webuser.getUid(req)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return webuser.page_not_authorized(req, "../youraccount.py/display")

    if webuser.isGuestUser(uid):		
	return page(title="Your Account",
                    body=webaccount.perform_info(req),
	            description="CDS Personalize, Main page",
	            keywords="CDS, personalize",
	            uid=uid,
                    language=ln,
                    lastupdated=__lastupdated__)

    data = webuser.getDataUid(req,uid)	
    bask = webbasket.account_list_baskets(uid)	  	  
    aler = webalert.account_list_alerts(uid)
    sear = webalert.account_list_searches(uid)	    	
    return page(title="Your Account",
                body=webaccount.perform_display_account(req,data,bask,aler,sear),
                description="CDS Personalize, Main page",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)
    	
def send_email(req, p_email=None, ln=cdslang):
    
    uid = webuser.getUid(req)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return webuser.page_not_authorized(req, "../youraccount.py/send_email")

    user_prefs = webuser.get_user_preferences(webuser.emailUnique(p_email))
    if user_prefs:
        if CFG_EXTERNAL_AUTHENTICATION.has_key(user_prefs['login_method']) or CFG_EXTERNAL_AUTHENTICATION.has_key(user_prefs['login_method']) and CFG_EXTERNAL_AUTHENTICATION[user_prefs['login_method']][0] != None:
	    Msg = """If you have lost password for your CERN Document Server internal
               account, then please enter your email address below and the lost
               password will be emailed to you.<br>
               Note that if you have been using an external login system (such
               as CERN NICE), then we cannot do anything and you have to ask
               there.  Alternatively, you can ask <a href="mailto:<%s>">
               <%s></a> to change your login system from external to internal.<br><br>""" % (supportemail, supportemail)

	    return page(title="Your Account",
                        body=Msg,
                        description="CDS Personalize, Main page",
                        keywords="CDS, personalize",
                        uid=uid,
                        language=ln,
                        lastupdated=__lastupdated__)

    passw = webuser.givePassword(p_email) 
    if passw == -999:
	eMsg = "The entered e-mail address doesn't exist in the database"
	return page(title="Your Account",
                    body=webaccount.perform_emailMessage(eMsg),
                    description="CDS Personalize, Main page",
                    keywords="CDS, personalize",
                    uid=uid,
                    language=ln,
                    lastupdated=__lastupdated__)
	
    fromaddr = "From: %s" % supportemail
    toaddrs  = "To: " + p_email
    to = toaddrs + "\n"
    sub = "Subject: Credentials for %s\n\n" % cdsname
    body = "Here are your user credentials for %s:\n\n" % cdsname
    body += "   username: %s\n   password: %s\n\n" % (p_email, passw)
    body += "You can login at %s/youraccount.py/login" % weburl
    msg = to + sub + body	

    server = smtplib.SMTP('localhost')
    server.set_debuglevel(1)
    
    try: 
	server.sendmail(fromaddr, toaddrs, msg)

    except smtplib.SMTPRecipientsRefused,e:
           eMsg = "The entered email address is incorrect, please check that it is written correctly (e.g. johndoe@example.com)."
	   return page(title="Incorrect email address",
                       body=webaccount.perform_emailMessage(eMsg),
                       description="CDS Personalize, Main page",
                       keywords="CDS, personalize",
                       uid=uid,
                       language=ln,
                       lastupdated=__lastupdated__)

    server.quit()
    return page(title="Lost password sent",
                body=webaccount.perform_emailSent(p_email),
                description="CDS Personalize, Main page",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def youradminactivities(req, ln=cdslang):
    uid = webuser.getUid(req)	

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return webuser.page_not_authorized(req, "../youraccount.py/youradminactivities")

    return page(title="Your Administrative Activities",
                body=webaccount.perform_youradminactivities(uid),
                navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">Your Account</a>""" % (weburl, ln),
                description="CDS Personalize, Main page",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def delete(req, ln=cdslang):
    uid = webuser.getUid(req)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return webuser.page_not_authorized(req, "../youraccount.py/delete")
	
    return page(title="Delete Account",
                body=webaccount.perform_delete(),
                navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">Your Account</a>""" % (weburl, ln),
                description="CDS Personalize, Main page",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)

def logout(req, ln=cdslang):
    
    uid = webuser.logoutUser(req)

    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return webuser.page_not_authorized(req, "../youraccount.py/logout")

    return page(title="Logout",
                body=webaccount.perform_logout(req),
                navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">Your Account</a>""" % (weburl, ln),
                description="CDS Personalize, Main page",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)
    
def login(req, p_email=None, p_pw=None, login_method=None, action='login', referer='', ln=cdslang):

    if CFG_ACCESS_CONTROL_LEVEL_SITE > 0:
        return webuser.page_not_authorized(req, "../youraccount.py/login")
        
    uid = webuser.getUid(req)

    if action =='login':
       if p_email==None or not login_method:
           return  page(title="Login",
                        body=webaccount.create_login_page_box(referer),
                        navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">Your Account</a>""" % (weburl, ln),
                        description="CDS Personalize, Main page",
                        keywords="CDS, personalize",
                        uid=uid,
                        language=ln,
                        lastupdated=__lastupdated__)
       (iden, p_email, p_pw, msgcode) = webuser.loginUser(req,p_email,p_pw, login_method)
       if len(iden)>0:
           
           uid = webuser.update_Uid(req,p_email,p_pw)
           uid2 = webuser.getUid(req)
           if uid2 == -1:
               webuser.logoutUser(req)
               return webuser.page_not_authorized(req, "../youraccount.py/login?ln=%s" % ln, uid=uid)

           # login successful!
           if referer:
               req.err_headers_out.add("Location", referer)
               raise apache.SERVER_RETURN, apache.HTTP_MOVED_PERMANENTLY               
           else:
               return display(req)
       else:
           mess = cfg_webaccess_warning_msgs[msgcode] % login_method
           if msgcode == 14:
      	       if not webuser.userNotExist(p_email,p_pw) or p_email=='' or p_email==' ':
                   mess = cfg_webaccess_warning_msgs[15] % login_method
           act = "login"    
	   return page(title="Login",
                       body=webaccount.perform_back(mess,act),
                       navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">Your Account</a>""" % (weburl, ln), 
                       description="CDS Personalize, Main page",
                       keywords="CDS, personalize",
                       uid=uid,
                       language=ln,
                       lastupdated=__lastupdated__)

def register(req, p_email=None, p_pw=None, p_pw2=None, action='login', referer='', ln=cdslang):

    if CFG_ACCESS_CONTROL_LEVEL_SITE > 0:
        return webuser.page_not_authorized(req, "../youraccount.py/register")

    uid = webuser.getUid(req)

    if p_email==None:
        return  page(title="Register",
                     body=webaccount.create_register_page_box(referer),
                     navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">Your Account</a>""" % (weburl, ln),
                     description="CDS Personalize, Main page",
                     keywords="CDS, personalize",
                     uid=uid,
                     language=ln,
                     lastupdated=__lastupdated__)
    
    mess=""
    act=""
    if p_pw == p_pw2:
        ruid = webuser.registerUser(req,p_email,p_pw)
    else:
        ruid = -2
    if ruid == 1:
        uid = webuser.update_Uid(req,p_email,p_pw)
        mess = "Your account has been successfully created."
        title = "Account created"
        if CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT == 1:
            mess += " An email has been sent to the given address with the account information."
        if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 1:
            mess += " A second email will be sent when the account has been activated and can be used."
        else:
            mess += """ You can now access your <a href="%s/youraccount.py/display?ln=%s">account</a>.""" % (weburl, ln)
    elif ruid == -1:
        mess = "The user already exists in the database, please try again."
	act = "register"
        title = "Register failure"
    elif ruid == -2:
        mess = "Both passwords must match, please try again."
	act = "register"
        title = "Register failure"
    else:
        mess = "The email address given is not valid, please try again."
       	act = "register"
        title = "Register failure"

    return page(title=title,
 	        body=webaccount.perform_back(mess,act),
                navtrail="""<a class="navtrail" href="%s/youraccount.py/display?ln=%s">Your Account</a>""" % (weburl, ln),
                description="CDS Personalize, Main page",
                keywords="CDS, personalize",
                uid=uid,
                language=ln,
                lastupdated=__lastupdated__)
