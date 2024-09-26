#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* Dictionary, currently english/german

********************************************************************

* Date                 : 2024-01-04
* Copyright            : (C) 2023 by Ludwig Kniprath
* Email                : ludwig at kni minus online dot de

********************************************************************

this program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

********************************************************************
"""
# Rev. 2024-01-04

from PyQt5 import QtCore, QtWidgets
import os, sys, pathlib, re
import sqlite3
import qgis

class SQLiteDict():
    """
    replacement for QtCore.QCoreApplication.translate(...), which is nearly impossible to maintain and has problems with markups
    used for all kinds of Qt-GUI-Strings e.g. ToolTips, Labels, messages...
    translations are supported via lcid
    Uses a single SQlite-DB/Table instead of previous storage in python-dicitionaries
    """
    # Rev. 2024-01-04
    # File-Name/Path
    sq3_db_file_name = 'SQLiteDict.sqlite3'
    sq3_table_name = 'snip_snippets'

    tr_dict = {}

    def __init__(self):
        """constructor
        connects and checks the SQLite-Database
        prepares a language dependend query
        :raises Exception: exceptionally, because dialogs and messages are not usable without this
        """
        # Rev. 2024-01-04
        try:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            # the db-file exists in the same directory:
            sq3_db_path = os.path.join(dir_path,self.sq3_db_file_name)
            # connect read only with uri instead of path
            # if the file does not exist:
            # raises sqlite3.OperationalError: unable to open database file
            # with path only a new database is created somewhere in Nirvana (bad experience...)
            uri = f'file:{sq3_db_path}?mode=ro'
            self.conn_sq3 = sqlite3.connect(uri,uri=True)
            self.cur_sq3 = self.conn_sq3.cursor()

            # check existance of the snippets-table:
            check_table_query = f"SELECT count(*) FROM sqlite_master where name=:table_name;"
            sqlite_result = self.cur_sq3.execute(check_table_query, {'table_name': self.sq3_table_name})
            sqlite_row = sqlite_result.fetchone()
            num_tables = sqlite_row[0]
            if num_tables < 1:
                raise Exception(f"LinearReference: SQLiteDict-Database '{self.sq3_db_file_name}' connected, but required table '{self.sq3_table_name}' missing...")

            # in QGis the "User interface translation" can differ from system-settings, if overrideFlag is set (Check-Box in QGis->Options->General "Overide System Locale")
            # additionally the Locale number/date/currency can be defined independently of "User interface translation" (affects among others decimal-point and seperator-char)
            # additionally the display of the dezimal-seperator (thousand, point or comma) can be toggled independently of number-format

            # Settings can be defined in QGis->Settings->Options->General
            # are stored in QGIS3.ini
            # are python-accessible via QtCore.QSettings()

            # language-change in System-Settings is directly reflected in QtCore.QSettings(), but the application must be reloaded to show the translation in GUI
            # despite the plugin will react on the changed settings by
            if QtCore.QSettings().value('locale/overrideFlag', type=bool):
                lcid = QtCore.QSettings().value('locale/userLocale', 'en_US')
            else:
                # take settings from system-locale, independent from current app
                lcid = QtCore.QLocale.system().name()

            # lcid is a string composed of language, underscore and country
            # for the translation the language is sufficient:
            # 'de_DE', 'de_AT', 'de_CH', 'de_BE', 'de_LI'... -> 'de'
            # 'en_US', 'en_GB'... -> 'en'
            lcid_language = lcid[0:2]

            # query the translation via parameterized snip_key
            # and/or query all translations and fill self.tr_dict

            # en-default in column snip_content_en
            self.query_single_sq3 = f"select snip_content_en from {self.sq3_table_name} where snip_key=:snip_key;"
            self.query_all_sq3 = f"select snip_key, snip_content_en from {self.sq3_table_name};"

            # de implemented
            if lcid_language == 'de':
                self.query_single_sq3 = f"select snip_content_de from {self.sq3_table_name} where snip_key=:snip_key;"
                self.query_all_sq3 = f"select snip_key, snip_content_de from {self.sq3_table_name};"

            # other languages can be easily implemented by adding *and filling* a translation-column
            # elif lcid_language == 'fr':
            #     self.query_single_sq3 = f"select snip_content_fr from {self.sq3_table_name} where snip_key=:snip_key;"
            # elif lcid_language == 'it':
            #     # italy
            #     self.query_single_sq3 = f"select snip_content_it from {self.sq3_table_name} where snip_key=:snip_key;"
            # elif lcid_language == 'es':
            #     # espania
            #     self.query_single_sq3 = f"select snip_content_es from {self.sq3_table_name} where snip_key=:snip_key;"
            # ...

            # get all translated snippets and fill self.tr_dict one time on init, necessary for tr-usage
            sqlite_result = self.cur_sq3.execute(self.query_all_sq3)

            records = sqlite_result.fetchall()
            for row in records:
                self.tr_dict[row[0]] = row[1]

        except sqlite3.OperationalError as e:
            raise Exception(f"LinearReference: SQLiteDict-Database '{self.sq3_db_file_name}' not found/connected in current directory: {e}...") from None

    def tr(self,snip_key, *embeds, **kwembeds)->str:
        """
        returns a translated snippet
        variant *without query* with pre-queried self.tr_dict
        pros: ca. 75 times faster
        cons: the translation-data is queried once and updates require a refresh of self.tr_dict
        The function raises no exception, but returns
            "?[{snip_key}]?" if the key is not found
            rsp. an error-message, if something goes wrong
        :param snip_key: key, for which the function searches in the snippet-dictionoary
        :param embeds: any number of arguments, which are stringified and embedded into the template via format-like wildcards {0} {1}...
        :param kwembeds: any number of keyword-arguments, which are stringified and embedded into the template via wildcard {key}...
        :returns: translated content with replacements
        """
        # Rev. 2024-01-08
        snip_content = self.tr_dict.get(snip_key, f'?[{snip_key}]?')
        return self.embed_wildcards(snip_content,embeds,kwembeds)


    def gs(self, snip_key, *embeds, **kwembeds)->str:
        """
        returns a translated snippet
        variant with individual SQLite-query of single snippet
        pros: usage, if the SQLite-translation-data could be altered on runtime
        cons: slow
        The function raises no exception, but returns
            "?[{snip_key}]?" if the key is not found
            rsp. an error-message, if something goes wrong


        :param snip_key: key, for which the function searches in the snippet-dictionoary
        :param embeds: any number of arguments, which are stringified and embedded into the template via format-like wildcards {0} {1}...
        :param kwembeds: any number of keyword-arguments, which are stringified and embedded into the template via wildcard {key}...
        :returns: translated content with replacements
        """
        # Rev. 2024-01-04
        snip_content = f'?[{snip_key}]?'

        try:
            # query_single_sq3 will query a language-specific column
            sqlite_result = self.cur_sq3.execute(self.query_single_sq3, {'snip_key': snip_key})

            sqlite_row = sqlite_result.fetchone()
            if sqlite_row:
                snip_content = sqlite_row[0]

        except sqlite3.OperationalError as e:
            # no exception, but error-message as returned string
            snip_content = f"Translation failed, SQLite-Error: '{e}'"
        except Exception as e:
            snip_content = f"Translation failed, Exception: '{e}'"

        return self.embed_wildcards(snip_content,embeds,kwembeds)



    def embed_wildcards(self,snip_content,embeds:list,kwembeds:dict)->str:
        """replace the optional format-like embeds,
        no error, if there are more/less/not-found embeds than wildcards
        each item in embeds will replace an incremented wildcard ala {0} {1}...
        each key-value-pair in kwembeds will replace a wildcard ala '{key}'...
        :param snip_content: queried snippet-content
        :param embeds: any number of arguments, which are stringified and embedded into the template via format-like wildcards {0} {1}...
        :param kwembeds: any number of keyword-arguments, which are stringified and embedded into the template via wildcard {key}...
        :returns: translated content with replacements
        """
        #
        #
        #
        ec = 0
        for e in embeds:
            s = '{' + str(ec) + '}'
            snip_content = snip_content.replace(s, str(e))
            ec += 1

        for key in kwembeds:
            s = '{' + key + '}'
            snip_content = snip_content.replace(s, str(kwembeds[key]))

        return snip_content



