#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3


def connectToDb():
    return sqlite3.connect('grades.db')


def getCursor(con):
    return con.cursor()


def createTables(cur):
    cur.execute('CREATE TABLE grades ('
                'course VARCHAR(255) PRIMARY KEY,'
                'grade VARCHAR(64)'
                ');')
