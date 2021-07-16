#!/usr/bin/env python
# -*- coding: utf-8 -*-
from urllib import error
from bs4 import BeautifulSoup
import traceback
import requests
import sqlite3
import telegram
import os
import sys
import initDB
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def findGrades(url, session):
    print("fetching data " + url)
    try:
        response = session.get(url)
    except:
        traceback.print_exc()
        print("Cannot connect to " + url)
        print(sys.exc_info())
        sys.exit(1)
    soup = BeautifulSoup(response.content, 'html.parser')
    tableRows = soup.findAll('tr', {'class': 'tbdata'})
    coursesAndGrades = []
    for row in tableRows:
        columns = row.findAll('td')
        courseName = ' '.join(str(columns[0].next).split())
        grade = ' '.join(str(columns[2].next).split())
        coursesAndGrades.append({'course': courseName, 'grade': grade})

    return coursesAndGrades


def logIn(url, payload):
    session = requests.Session()
    print('get user credentials from ' + url)
    try:
        response = session.post(url, data=payload)
    except:
        traceback.print_exc()
        print("Cannot connect to " + url)
        print(sys.exc_info())
        sys.exit(1)

    return ['https://almaweb.uni-leipzig.de' + response.headers._store['refresh'][1].split('; URL=')[1], session]


def figureOutURL(url, session, textToSearchFor):
    print("find url to " + textToSearchFor)
    try:
        response = session.get(url)
    except:
        traceback.print_exc()
        print("Cannot connect to " + url)
        print(sys.exc_info())
        sys.exit(1)
    soup = BeautifulSoup(response.content, 'html.parser')
    url = soup.find('a', text = textToSearchFor)

    return url.get('href')


def checkIfDBIsThere(cur):
    print("checking if db has been initialized yet")
    try:
        cur.execute('SELECT course FROM grades limit 1')
    except sqlite3.OperationalError as e:
        print(f"db has not been initialized yet: {e}")
        initDB.createTables(cur)
    else:
        print("db has been initialized")

        return 0


def insertOrIgnoreGrade(cur, con, gradesDict, bot):
    try:
        for row in gradesDict:
            cur.execute('SELECT grade FROM grades WHERE course=?', (row['course'],))
            res = cur.fetchone()
            if res is None:
                cur.execute('INSERT INTO grades VALUES(?,?)', (row['course'], row['grade']))
                con.commit()
                sendTelegramMessage(bot, 'new grade in ' + row['course'] + ' -> ' + row['grade'])
            else:
                print('grade is already in db')
    except sqlite3.OperationalError as e:
        print(f"error while working with db: {e}")
        print("exiting")
        print(sys.exc_info())
        sys.exit(1)


def sendTelegramMessage(bot, text):
    print("send telegram message")
    bot.send_message(chat_id=os.environ['TELEGRAM_CHAT_ID'], text=text)

    return 0


def initTelegramBot():
    print("initialize telegram bot")
    return telegram.Bot(token=os.environ['TELEGRAM_TOKEN'])


def main():
    print("---")
    try:
        #check if script in running in docker container
        print("starting bot for username: " + os.environ['ALMAWEB_USERNAME'])
    except KeyError:
        load_dotenv()
        print("starting bot for username: " + os.environ['ALMAWEB_USERNAME'])
    print("utc time now: " + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))

    loginPayload = {
        'usrname': os.environ['ALMAWEB_USERNAME'],
        'pass': os.environ['ALMAWEB_PASSWORD'],
        'APPNAME': 'CampusNet',
        'PRGNAME': 'LOGINCHECK',
        'ARGUMENTS': 'clino,usrname,pass,menuno,menu_type,browser,platform',
        'clino': '000000000000001',
        'menuno': '000299',
        'menu_type': 'classic',
        'browser': 'platform'
    }

    try:
        bot = initTelegramBot()
        con = initDB.connectToDb()
        cur = initDB.getCursor(con)
        checkIfDBIsThere(cur)
        redirectAndSession = logIn('https://almaweb.uni-leipzig.de/scripts/mgrqispi.dll', loginPayload)
        landingPageUrl = figureOutURL(redirectAndSession[0], redirectAndSession[1], 'Startseite')
        studiesUrl = figureOutURL('https://almaweb.uni-leipzig.de' + landingPageUrl, redirectAndSession[1], 'Studium')
        resultsUrl = figureOutURL('https://almaweb.uni-leipzig.de' + studiesUrl, redirectAndSession[1],
                                  'Prüfungsergebnisse')
        response = findGrades('https://almaweb.uni-leipzig.de' + resultsUrl, redirectAndSession[1])
        insertOrIgnoreGrade(cur, con, response, bot)
    except requests.exceptions.RequestException as e:
        print(f"Cannot connect to webservice: {e}")
        traceback.print_exc()
        print("exiting")
        print(sys.exc_info())
        sys.exit(1)
    except telegram.TelegramError as e:
        print(f"error while working with telegram api: {e}")
        traceback.print_exc()
        print("exiting")
        print(sys.exc_info())
        sys.exit(1)


if __name__ == '__main__':
    main()


