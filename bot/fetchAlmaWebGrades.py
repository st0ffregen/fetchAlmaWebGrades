#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import sqlite3
import telegram
import os
import initDB
from dotenv import load_dotenv
import logging
import json


load_dotenv()


def findGrades(url, session):
    response = session.get(url)
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
    response = session.post(url, data=payload)

    return response.headers._store['refresh'][1].split('&ARGUMENTS=')[1], session


def isDBThere(cur):
    try:
        cur.execute('SELECT course FROM grades limit 1')
    except sqlite3.OperationalError as e:
        print(f"db has not been initialized yet: {e}")
        return False

    return True


def getNewGradesFromResponse(cur, gradesDict):
    newGrades = []
    for row in gradesDict:
        cur.execute('SELECT grade FROM grades WHERE course=?', (row['course'],))
        res = cur.fetchone()
        if res is None:
            newGrades.append({
                'course': row['course'],
                'grade': row['grade']
            })

    return newGrades


def insertNewGrades(cur, con, gradesDict):
    for grade in gradesDict:
        cur.execute('INSERT INTO grades VALUES(?,?)', (grade['course'], grade['grade']))
    con.commit()


def sendTelegramMessage(bot, gradeDict):
    bot.send_message(chat_id=os.environ['TELEGRAM_CHAT_ID'], text=json.dumps(gradeDict))


def initTelegramBot():
    return telegram.Bot(token=os.environ['TELEGRAM_TOKEN'])


def configureLogger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

    file_handler = logging.FileHandler('logs/fetchAlmaWebGrades.log')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger


def main():
    logger = configureLogger()
    username = os.environ['ALMAWEB_USERNAME']
    logger.info('start fetch almaweb grades bot for user ' + username)

    loginPayload = {
        'usrname': username,
        'pass': os.environ['ALMAWEB_PASSWORD'],
        'APPNAME': 'CampusNet',
        'PRGNAME': 'LOGINCHECK',
        'ARGUMENTS': 'clino,usrname,pass,menuno,menu_type,browser,platform',
        'clino': '000000000000001',
        'menuno': '000299',
        'menu_type': 'classic',
        'browser': 'platform'
    }

    con = initDB.connectToDb()
    cur = initDB.getCursor(con)

    if isDBThere(cur) is False:
        logger.info('init db')
        initDB.createTables(cur)

    paramString, session = logIn('https://almaweb.uni-leipzig.de/scripts/mgrqispi.dll', loginPayload)
    response = findGrades(
        'https://almaweb.uni-leipzig.de/scripts/mgrqispi.dll?APPNAME=CampusNet&PRGNAME=EXAMRESULTS&ARGUMENTS=' + paramString,
        session)

    newGrades = getNewGradesFromResponse(cur, response)
    logger.info('new grades: ' + json.dumps(newGrades))
    if len(newGrades) > 0:
        insertNewGrades(cur, con, newGrades)
        bot = initTelegramBot()
        sendTelegramMessage(bot, newGrades)


if __name__ == '__main__':
    main()
