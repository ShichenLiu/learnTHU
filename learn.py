# Lustralisk
# !usr/bin/python
# coding: UTF-8

# sdk
# function:
#   get course informations
#   
# request packages: beautiful soup

# improvement:
#     how to make sure login successful
#     notice_new, pages can be more than one
#     new version use ajax, do something
#     to speed up, recommend some courses into blacklist, e.g. 文化素质讲座
#     appendfile download

import sys
reload(sys)
sys.setdefaultencoding("utf8")
import requests
import urllib
import urllib2
import time
from bs4 import BeautifulSoup
import os
import re
import json
import shutil
from progressbar import AnimatedMarker, Bar, BouncingBar, Counter, ETA, \
                        FileTransferSpeed, FormatLabel, Percentage, \
                        ProgressBar, ReverseBar, RotatingMarker, \
                        SimpleProgress, Timer

# demo
USER_INFO = {
    "userid" : "",
    "userpass" : "",
}
FILE_PATH = "/Users/lustralisk/desktop/test"
DATABASE_PATH = "/Users/lustralisk/desktop/test"


# global variable
ROOT = "http://learn.tsinghua.edu.cn"
ROOT_S = "https://learn.tsinghua.edu.cn"
ROOT_NEW = "http://learn.cic.tsinghua.edu.cn"
URL = {
    "test_new": "http://learn.cic.tsinghua.edu.cn/f/student/coursehome/2014-2015-2-10430484-10",
    "login": "/MultiLanguage/lesson/teacher/loginteacher.jsp",
    "login_new": "https://id.tsinghua.edu.cn/do/off/ui/auth/login/post/fa8077873a7a80b1cd6b185d5a796617/0?/j_spring_security_thauth_roaming_entry",
    "dashboard": "/MultiLanguage/lesson/student/MyCourse.jsp?language=cn",
    "home_new": "/f/student/coursehome/",
    "assignment": "/MultiLanguage/lesson/student/hom_wk_brw.jsp?course_id=",
    "assignment_new_1": "/b/myCourse/homework/list4Student/",
    "assignment_new_2": "/0",
    "notice": "/MultiLanguage/public/bbs/getnoteid_student.jsp?course_id=",
    "notice_new": "/b/myCourse/notice/listForStudent/",
    "file": "/MultiLanguage/lesson/student/download.jsp?course_id=",
    "notice_detail_1": "/MultiLanguage/public/bbs/note_reply.jsp?bbs_type=课程公告&id=",
    "notice_detail_2": "&course_id=",
    "notice_detail_new": "/b/myCourse/notice/studDetail/",
    "assignment_detail_1": "/MultiLanguage/public/bbs/note_reply.jsp?bbs_type=课程公告&id=",
    "assignment_detail_2": "&course_id=",
    "assignment_detail_new": "/b/myCourse/homeworkRecord/getByHomewkIdAndStuId/",
}


COURSE_BLACKLIST = ["122360", "125938", "122401"]
NOTICE_BLACKLIST = ["122641"]
ASSIGNMENT_BLACKLIST = ["122350"]
FILE_BLACKLIST = []


# helper function

def loading_bar(i, text):
    print '\r',
    sys.stdout.flush()
    print '\r' + '#'*(i/2) + ' '*(50 - i/2) + str(i) + '% ' + text,
    sys.stdout.flush()
    return

def shape(s):
    if s:
        start = 0
        end = 0
        for i in range(len(s)):
            if s[i] != "\n" and s[i] != "\r" and s[i] != "\t" and s[i] != " ":
                start = i
                break
        for i in range(len(s))[::-1]:
            if s[i] != "\n" and s[i] != "\r" and s[i] != "\t" and s[i] != " ":
                end = i + 1
                break
        return s[start:end]
    else:
        return ""

class Learn:

    def api_course_notices(self, course_id, course_new):
        if course_id not in NOTICE_BLACKLIST:
            notices = []
            if course_new:
                notices_session = self.session.get(ROOT_NEW + URL["notice_new"] + course_id)
                notice_objs = json.loads(notices_session.text)["paginationList"]["recordList"]

                for notice_obj in notice_objs:
                    cell_obj = notice_obj["courseNotice"]
                    notice = {}
                    notice["type"] = "notice"
                    notice["title"] = cell_obj["title"]
                    notice["uploader"] = cell_obj["owner"]
                    notice["time_stamp"] = cell_obj["regDate"]
                    notice["id"] = str(cell_obj["id"])
                    notice["course_id"] = course_id
                    notice["new"] = True

                    notices.append(notice)
                    notice["state"] = "read"
                    if notice_obj["status"].strip(' ') == "0":
                        notice["state"] = "new"
            else:
                notices_session = self.session.get(ROOT + URL["notice"] + course_id)
                notices_HTML = BeautifulSoup(notices_session.text)
                notice_objs = notices_HTML.find(id = "table_box").find_all("tr")

                for notice_obj in [notice_obj for notice_obj in notice_objs if notice_obj.get("class", "") != ""]:
                    cell_objs = notice_obj.find_all("td")
                    notice = {}
                    notice["type"] = "notice"
                    notice["title"] = shape(cell_objs[1].a.string)
                    notice["uploader"] = shape(cell_objs[2].string)
                    notice["time_stamp"] = shape(cell_objs[3].string)
                    notice["id"] = re.search("\d+", cell_objs[1].a.get("href")).group(0)
                    notice["course_id"] = course_id
                    notice["new"] = False

                    notices.append(notice)
                    notice["state"] = "read"
                    if cell_objs[4].string == "未读":
                        notice["state"] = "new"
            return notices
        else:
            return []

    def api_course_assignments(self, course_id, course_new):
        if course_id not in ASSIGNMENT_BLACKLIST:
            assignments = []
            if course_new:
                assignments_session = self.session.get(ROOT_NEW + URL["assignment_new_1"] + course_id + URL["assignment_new_2"])
                assignment_objs = json.loads(assignments_session.text)["resultList"]
                for assignment_obj in assignment_objs:
                    cell_objs = assignment_obj["courseHomeworkInfo"]
                    assignment = {}
                    assignment["type"] = "assignment"
                    assignment["title"] = cell_objs["title"]
                    assignment["time_stamp"] = time.strftime("%m-%d %H:%M",time.localtime(int(str(cell_objs["beginDate"])[:-3])))
                    assignment["deadline"] = time.strftime("%m-%d %H:%M",time.localtime(int(str(cell_objs["endDate"])[:-3])))
                    assignment["id"] = cell_objs["homewkId"]
                    assignment["course_id"] = course_id
                    if assignment["deadline"] < time.strftime("%m-%d %H:%M",time.localtime()):
                        assignment["state"] = "miss"
                    elif assignment_obj["courseHomeworkRecord"]["status"] >= 2:
                        assignment["state"] = "done"
                    elif assignment_obj["courseHomeworkRecord"]["status"] == 1:
                        assignment["state"] = "uploaded"
                    else:
                        assignment["state"] = "not_finish"
                    assignment["new"] = True

                    assignments.append(assignment)
            else:
                assignments_session = self.session.get(ROOT + URL["assignment"] + course_id)
                assignments_HTML = BeautifulSoup(assignments_session.text)
                assignment_objs = assignments_HTML.find(id = "info_1").find_all("tr")[2].td.find_all("table")[1].find_all("tr")

                for assignment_obj in [assignment for assignment in assignment_objs if assignment.get("class", "") != ""]:
                    cell_objs = assignment_obj.find_all("td")
                    assignment = {}
                    assignment["type"] = "assignment"
                    assignment["title"] = shape(cell_objs[0].a.string)
                    assignment["time_stamp"] = shape(cell_objs[1].string)
                    assignment["deadline"] = shape(cell_objs[2].string)
                    assignment["id"] = re.search("\d+", cell_objs[0].a.get("href")).group(0)
                    assignment["course_id"] = course_id
                    if shape(cell_objs[3].string) == "尚未提交":
                        if cell_objs[5].find_all("input")[0].get("disabled", "") == "":
                            assignment["state"] = "not_finish"
                        else:
                            assignment["state"] = "miss"
                    else:
                        if cell_objs[5].find_all("input")[0].get("disabled", "") == "":
                            assignment["state"] = "uploaded"
                        elif cell_objs[5].find_all("input")[1].get("disabled", "") == "":
                            assignment["state"] = "done"
                        else:
                            assignment["state"] = "judging"
                    assignment["new"] = False
                    assignments.append(assignment)
            return assignments
        else:
            return []

    def api_course_files(self, course_id, course_new):
        if course_id not in FILE_BLACKLIST:
            files = []
            if course_new:
                pass
            else:
                files_session = self.session.get(ROOT + URL["file"] + course_id)
                files_HTML = BeautifulSoup(files_session.text)
                file_objs = files_HTML.find(id = "table_box").find_all("tr")
                for file_obj in [file_obj for file_obj in file_objs if file_obj.get("class", "") != ""]:
                    cell_objs = file_obj.find_all("td")
                    file = {}
                    file["type"] = "file"
                    file["title"] = shape(cell_objs[1].a.string or cell_objs[1].a.font.string)
                    file["discription"] = shape(cell_objs[2].string)
                    file["size"] = shape(cell_objs[3].string)
                    file["timeStamp"] = shape(cell_objs[4].string)
                    file["href"] = cell_objs[1].a.get("href")
                    file["id"] = re.search("\d+$", cell_objs[1].a.get("href")).group(0)
                    file["course_id"] = course_id
                    file["state"] = "downloaded"
                    if "新文件" in cell_objs[5].string:
                        file["state"] = "new"
                    files.append(file)
        else:
            return []

    def api_notice_detail(self, notice):
        notice_detail = {}
        notice_detail["id"] = notice["id"]
        notice_detail["course_id"] = notice["course_id"]
        notice_detail["uploader"] = notice["uploader"]
        notice_detail["time_stamp"] = notice["time_stamp"]
        if notice["new"]:
            detail_session = self.session.get(ROOT_NEW + URL["notice_detail_new"] + notice["id"])
            detail_obj = json.loads(detail_session.text)["dataSingle"]

            notice_detail["title"] = detail_obj["title"]
            notice_detail["detail"] = detail_obj["detail"]

        else:
            detail_session = self.session.get(ROOT + URL["notice_detail_1"] + notice["id"] + URL["notice_detail_2"] + notice["course_id"])
            detail_HTML = BeautifulSoup(detail_session.text)
            detail_obj = detail_HTML.find(id = "table_box").find_all("tr")

            notice_detail["title"] = shape(detail_obj[0].find_all("td")[1].string)
            notice_detail["detail"] = shape(detail_obj[1].find_all("td")[1].string)

        return notice_detail

    def api_assignment_detail(self, assignment):
        assignment_detail = {}
        assignment_detail["id"] = assignment["id"]
        assignment_detail["course_id"] = assignment["course_id"]
        assignment_detail["time_stamp"] = assignment["time_stamp"]
        if assignment["new"]:
            detail_session = self.session.get(ROOT_NEW + URL["assignment_detail_new"] + assignment["id"])
            detail_obj = json.loads(detail_session.text)["result"]["courseHomeworkInfo"]

            assignment_detail["title"] = detail_obj["title"]
            assignment_detail["detail"] = detail_obj["detail"]
            assignment_detail["file_url"] = ""

        else:
            detail_session = self.session.get(ROOT + URL["assignment_detail_1"] + assignment["id"] + URL["assignment_detail_2"] + assignment["course_id"])
            detail_HTML = BeautifulSoup(detail_session.text)
            detail_obj = detail_HTML.find(id = "table_box").find_all("tr")

            assignment_detail["title"] = shape(detail_obj[0].find_all("td")[1].string)
            assignment_detail["detail"] = shape(detail_obj[1].find_all("td")[1].find("textarea").string) if detail_obj[1].find_all("td")[1].find("textarea") else ""
            assignment_detail["file_url"] = shape(detail_obj[2].find_all("td")[1].find("a").get("href")) if detail_obj[2].find_all("td")[1].find("a") else ""

        return assignment_detail

    def api_download(self, url, path, filename):
        print "downloading " + filename
        r = self.session.get(url, stream = True)
        with open(path + filename, "wb") as fout:
            shutil.copyfileobj(r.raw, fout)
        return

    def show_notice(self, notice, appendix = "", prefix = "", detail = False):
        if detail:
            if notice["course_id"] not in self.notice_singles:
                self.notice_singles[notice["course_id"]] = {}
            if notice["id"] not in self.notice_singles[notice["course_id"]]:
                obj = self.notice_singles[notice["course_id"]][notice["id"]] = self.api_notice_detail(notice)
            else:
                obj = self.notice_singles[notice["course_id"]][notice["id"]]
            print "%s--%s--%s" % (obj["title"], obj["uploader"], obj["time_stamp"])
            print "    %s" % (obj["detail"])
        else:
            print prefix + notice["title"] + appendix
        print '\n'
        return

    def show_assignment(self, assignment, prefix = "", detail = False):
        if detail:
            print assignment["title"] + '-' + assignment["state"] + '       ' + assignment["deadline"]
        else:
            print prefix + assignment["title"]
        return

    def show_file(self, file, prefix = "", detail = False):
        print prefix + file["title"]
        return

    def show_course(self, course, detail = False):
        if detail == True:
            print course["name"]
            print course["notice_count"] + "个公告"
            for notice in course["notice"]:
                self.show_notice(notice, prefix = "    ")
            print course["assignment_count"] + "个未交作业 "
            for assignment in course["assingment"]:
                self.show_assignment(assignment, prefix = "    ")
            print course["file_count"] + "个新文件"
            for file in course["file"]:
                self.show_file(file, prefix = "    ")
        else:
            print course["name"] + '[' + course["id"] + ']' + ' ' + course["notice_count"] + "个公告 " + course["assignment_count"] + "个未交作业 " + course["file_count"] + "个新文件"
        return

    def cmd_filter(self, _subject, course_id = -1, course_name = "", id = -1, name = "", before = "", after = "", new = ""):
        re = []
        subjects = _subject.split(' ')

        for course in self.courses:
            if course["id"] not in COURSE_BLACKLIST:
                if not (course_id != -1 and course_id != course["id"]):
                    for subject in subjects:
                        if course["id"] not in eval(subject.upper() + "_BLACKLIST"):
                            for term in course[subject]:
                                if not (id != -1 and id != term["id"]):
                                    if not (name != "" and name not in term["title"]):
                                        if not (course_name != "" and course_name not in course["name"]):
                                            if not (before and term["time_stamp"] > before):
                                                if not (after and term["time_stamp"] < after):
                                                    if not (new and not (term["state"] == "new" or term["state"] == "not_finish")):
                                                        re.append(term)
        return re

    def cmd_directive(self, re, first_order = "", second_order = ""):
        if first_order:
            order_1 = first_order.split('-')[0]
            order_1_greater = first_order.split('-')[1] == "greater"
        else:
            order_1 = ""
        if second_order:
            order_2 = second_order.split('-')[0]
            order_2_greater = second_order.split('-')[1] == "greater"
        else:
            order_2 = ""

        def cmp(a, b):
            if order_1:
                if not order_1_greater ^ (a[order_1] > b[order_1]):
                    return 1
                elif not order_1_greater ^ (a[order_1] < b[order_1]):
                    return -1
                elif order_2:
                    if not order_2_greater ^ (a[order_2] > b[order_2]):
                        return 1
                    elif not order_2_greater ^ (a[order_2] < b[order_2]):
                        return -1
                    else:
                        return 0
                else:
                    return 0

        return sorted(re, cmp)

    def cmd_get(self, cmd, args = {}):
        if cmd == "course":
            for course in self.courses:
                if not (("new" in args) and course["assignment_count"] + course["notice_count"] + course["file_count"] == 0):
                    if not (("course_id" in args) and course["id"] != args["course_id"]):
                        if not (("course_name" in args) and args["course_name"] not in course["name"]):
                            self.show_course(course)
        elif cmd in ["notice", "assignment", "file"]:
            filter = {}
            for term in ["id", "name", "course_id", "course_name", "before", "after", "new"]:
                if term in args:
                    filter[term] = args[term]
            temp = self.cmd_filter(cmd, **filter)
            director = {}
            for term in ["first_order", "second_order"]:
                if term in args:
                    director[term] = args[term]
            if director:
                temp = self.cmd_directive(temp, **director)
            for obj in temp:
                eval("show_" + obj["type"])(obj, detail = True)

    def cmd_parse(self, input):
        cmds = input.split()
        cmds.append('#')

        filter = {}

        if cmds[0] == "get":
            for i in range(2, len(cmds)):
                if cmds[i][0] == '-':
                    filter[cmds[i][1:]] = cmds[i + 1]

            self.cmd_get(cmds[1], filter)

    def login(self):
        print "logging in..."
        try:
            session = requests.Session()
            submit = {
                "userid": USER_INFO["userid"],
                "userpass": USER_INFO["userpass"],
                "submit1": "登录",
            }
            re = session.post(ROOT_S + URL["login"], submit)
            submit1 = {
                "i_user": USER_INFO["userid"],
                "i_pass": USER_INFO["userpass"],
            }
            while 1:
                session.post(URL["login_new"], submit1)
                if session.get(URL["test_new"]).status_code != 500:
                    break
        except:
            print "log in failed"
            exit()
        print "successful logging in"
        return session

    def prepare(self):
        print "loading..."

        # create working path
        if not os.path.exists(DATABASE_PATH):
            os.mkdir(DATABASE_PATH)
        os.chdir(DATABASE_PATH)

        # load files
        if not os.path.exists("database.db"):
            fin = open("database.db", 'w')
            fin.close()

        fin = open("database.db", 'r')
        content = fin.read()
        fin.close()

        try:
            obj = json.loads(content)
            NOTICES, ASSIGNMENTS, FILES = (obj.get("notices", {}), obj.get("assignments", {}), obj.get("files", {}))
        except ValueError:
            NOTICES, ASSIGNMENTS, FILES = ({}, {}, {})

        print "finish loading..."

        return NOTICES, ASSIGNMENTS, FILES

    def initialize(self):
        print "initializing..."

        COURSES = []
        NOTICES = {}
        ASSIGNMENTS = {}
        FILES = {}

        dashboard_session = self.session.get(ROOT + URL["dashboard"])
        dashboard_HTML = BeautifulSoup(dashboard_session.text)
        dashboard = dashboard_HTML.find(id = "info_1")
        course_objs = [course_obj for course_obj in dashboard.children if course_obj != '\n' and course_obj.get("class", '') != '']

        for course_obj in course_objs:

            course = {}

            rawName = course_obj.a.string
            course["name"] = shape(re.search("[^\(]*", rawName).group(0))
            course["period"] = shape(re.search("\(2.*\)", rawName).group(0)[1:-1])

            if course_obj.span.string == "(新版)":
                course["new"] = True
            else:
                course["new"] = False

            loading_bar(100*len(COURSES)/(len(course_objs) - len(COURSE_BLACKLIST)), course["name"] + "...")

            terms = course_obj.find_all("span")
            course["assignment_count"] = terms[1].string
            course["notice_count"] = terms[2].string
            course["file_count"] = terms[3].string

            if course["new"]:
                course["id"] = re.search("[^/]+$", course_obj.find("a").get("href")).group(0)
            else:
                course["id"] = re.search("\d+$", course_obj.find("a").get("href")).group(0)

        self.cmd_get("course")



        for course_obj in course_objs:

            if course["id"] not in COURSE_BLACKLIST:

                # update
                if course["id"] not in NOTICE_BLACKLIST:
                    course["notice"] = self.api_course_notices(course["id"], course["new"])
                    NOTICES[course["id"]] = [notice for notice in course["notice"] if notice["state"] == "new"]
                else:
                    course["notice"] = []

                if course["id"] not in ASSIGNMENT_BLACKLIST:
                    course["assignment"] = self.api_course_assignments(course["id"], course["new"])
                    ASSIGNMENTS[course["id"]] = [assignment for assignment in course["assignment"] if assignment["state"] == "not_finish"]
                else:
                    course["assignment"] = []

                if course["id"] not in FILE_BLACKLIST:
                    course["file"] = self.api_course_files(course["id"], course["new"])
                    FILES[course["id"]] = [file for file in course["file"] if file["state"] == "new"]
                else:
                    course["file"] = []

            # update

            # notices
            course["notice"] = []



            # assignments
            course["assignment"] = []



            # files
            course["file"] = []

            if not course["id"] in FILE_BLACKLIST:

                FILES[course["id"]] = []

                if course["new"]:
                    pass

                else:
                    files_session = self.session.get(ROOT + URL["file"] + course["id"])
                    files_HTML = BeautifulSoup(files_session.text)
                    file_objs = files_HTML.find(id = "table_box").find_all("tr")

                    for file_obj in [file_obj for file_obj in file_objs if file_obj.get("class", "") != ""]:
                        cell_objs = file_obj.find_all("td")
                        file = {}
                        file["type"] = "file"
                        file["title"] = shape(cell_objs[1].a.string or cell_objs[1].a.font.string)
                        file["discription"] = shape(cell_objs[2].string)
                        file["size"] = shape(cell_objs[3].string)
                        file["timeStamp"] = shape(cell_objs[4].string)
                        file["href"] = cell_objs[1].a.get("href")
                        file["id"] = re.search("\d+$", cell_objs[1].a.get("href")).group(0)
                        file["course_id"] = course["id"]
                        file["state"] = "none"
                        file["new"] = False

                        course["file"].append(file)
                        if "新文件" in cell_objs[5].string:
                            FILES[course["id"]].append(file)

            else:
                pass

            COURSES.append(course)

        print "finish initializing..."

        return (COURSES, NOTICES, ASSIGNMENTS, FILES)

    def save(self):

        # file path
        if not os.path.exists(DATABASE_PATH):
            os.makdir(DATABASE_PATH)
        os.chdir(DATABASE_PATH)

        obj = {"notice": self.notice_singles, "assignments": self.assignment_singles, "files": self.file_singles}

        fin = open("database.db", "w")
        fin.write(json.dumps(obj))

        fin.close()
        return

    def __init__(self):

        self.notice_singles, self.assignment_singles, self.file_singles = self.prepare()

        self.session = self.login()

        self.courses, self.notices, self.assignments, self.files = self.initialize

        return

    def work(self):

        while 1:
            input = raw_input(">>>")
            if input != "exit":
                self.cmd_parse(input)
            else:
                break
            self.save()

        return



learn = Learn()

learn.work()
