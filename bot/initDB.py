#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
import sys



def connectToDb():
    try:
        con = sqlite3.connect('grades.db')
        return con
    except sqlite3.OperationalError as e:
        print(f"error while establishing connection to db: {e}")
        print("exiting")
        print(sys.exc_info())
        sys.exit(1)


def getCursor(con):
    try:
        return con.cursor()
    except sqlite3.OperationalError as e:
        print(f"error while creating cursor for connection: {e}")
        print("exiting")
        print(sys.exc_info())
        sys.exit(1)


def createTables(cur):
    print("creating tables in db")
    try:
        cur.execute('CREATE TABLE grades ('
                    'course VARCHAR(255) PRIMARY KEY,'
                    'grade VARCHAR(64)'
                    ');')
    except sqlite3.OperationalError as e:
        print(f"error while inserting new tables to db: {e}")
        print("exiting")
        print(sys.exc_info())
        sys.exit(1)

    return 0
