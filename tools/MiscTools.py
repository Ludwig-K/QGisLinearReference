#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* some Helper-Tools for command-line-usage

********************************************************************

* Date                 : 2024-09-26
* Copyright            : (C) 2024 by Ludwig Kniprath
* Email                : ludwig at kni minus online dot de

********************************************************************

this program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

********************************************************************
"""


import os, sys, pathlib, re, sqlite3

# scan all svg-icons in directory \QGIS\QGIS3\profiles\default\python\plugins\LinearReferencing\icons\
# /usr/bin/python3 /home/ludwig/.local/share/QGIS/QGIS3/profiles/default/python/plugins/LinearReferencing/tools/MiscTools.py scan_icon_usages
# /usr/bin/python3 /home/ludwig/.local/share/QGIS/QGIS3/profiles/default/python/plugins/LinearReferencing/tools/MiscTools.py scan_icon_usages delete_unfound

# scan all images in directory \plugins\LinearReferencing\docs\images\
# /usr/bin/python3 /home/ludwig/.local/share/QGIS/QGIS3/profiles/default/python/plugins/LinearReferencing/tools/MiscTools.py scan_html_image_usages
# /usr/bin/python3 /home/ludwig/.local/share/QGIS/QGIS3/profiles/default/python/plugins/LinearReferencing/tools/MiscTools.py scan_html_image_usages delete_unfound

# find all usages of MY_DICT
# /usr/bin/python3 /home/ludwig/.local/share/QGIS/QGIS3/profiles/default/python/plugins/LinearReferencing/tools/MiscTools.py scan_dict_usages
# /usr/bin/python3 /home/ludwig/.local/share/QGIS/QGIS3/profiles/default/python/plugins/LinearReferencing/tools/MiscTools.py scan_dict_usages delete_missing

if __name__ == "__main__":
    on_load_task = None
    on_load_param_1 = None
    # sys.argv => path of current script
    if len(sys.argv) == 2:
        on_load_task = sys.argv[1]

    if len(sys.argv) == 3:
        on_load_task = sys.argv[1]
        on_load_param_1 = sys.argv[2]

    print(on_load_task,on_load_param_1)

    if on_load_task == "scan_icon_usages":
        # scans all svg-icons in directory \QGIS\QGIS3\profiles\default\python\plugins\LinearReferencing\icons\
        # optionally deletes not used ones
        # Note: these icons are used in python via pyrcc5 bundled resource-file,
        # configured by an XML-File profiles\default\python\plugins\LinearReferencing\icons\resources.qrc
        # they are used inside python and identified below via QtGui.QIcon(':icons/linear_referencing_point.svg')
        # resources.qrc has to be adapted afterward (delete lines with deleted svgs) and the resource-file has to be pyrcc5-re-generated


        # current executed script:
        path = pathlib.Path(__file__)
        parent = path.parent.parent.absolute()


        # recursively find scan-targets: all python-files in parent.parent
        scan_files = [str(file) for file in parent.rglob('*.py')]

        # do not scan these python-files:
        skip_files = [
            # the pyrcc5-compiled resources
            'resources.py'
        ]

        skip_icons = [
            # used as Plugin-Icon outside python, see metadata.txt
            'linear_referencing.svg'
        ]

        # find all icon-files in a directory, type svg
        icon_path = pathlib.Path(os.path.join(parent, 'icons'))

        svg_files = [str(file) for file in icon_path.rglob('*.svg')]

        svg_files = sorted(svg_files,key=str.casefold)


        hit_list = {}
        for abs_path in svg_files:
            file_name = os.path.basename(abs_path)
            if file_name not in skip_icons:
                search_string =  f":icons/{file_name}"
                if search_string not in skip_files:
                    hit_list[abs_path] = []
                    for c_path in scan_files:
                        with open(c_path, 'r') as fp:
                            if search_string in fp.read():
                                fp.seek(0)
                                for l_no, line in enumerate(fp):
                                    if search_string in line:
                                        hit_list[abs_path].append([c_path,l_no])



        found_result = ""
        not_found_result = ""
        for abs_path in hit_list:
            trunc_abs_path = abs_path.replace(str(parent),'')

            if len(hit_list[abs_path]):
                found_path = str(hit_list[abs_path][0][0])
                rel_path = found_path.replace(str(parent),'')

                line = hit_list[abs_path][0][1]
                found_result += f"{trunc_abs_path} -> {rel_path} #{line}\n"
            else:
                not_found_result += f"{trunc_abs_path}"
                if on_load_param_1 == 'delete_unfound':
                    if os.path.isfile(abs_path):
                        try:
                            os.remove(abs_path)
                            not_found_result += " ... deleted"
                        except:
                            not_found_result += "... could not be deleted"

                not_found_result += "\n"



        print("not found:\n",not_found_result)

        print("found:\n",found_result)


    elif on_load_task == "scan_html_image_usages":
        # scans all images in directory \plugins\LinearReferencing\docs\images\
        # find usages in the two html-files index.en.html rsp. index.de.html
        # optionally deletes not used images

        # current executed script:
        path = pathlib.Path(__file__)
        parent = path.parent.parent.absolute()


        # recursively find scan-targets: all html and css-files in parent.parent.docs
        docs_path = pathlib.Path(os.path.join(parent, 'docs'))
        scan_files = [str(file) for file in docs_path.rglob('*.html')]
        scan_files += [str(file) for file in docs_path.rglob('*.css')]


        # do not scan these files:
        skip_files = [

        ]

        # do not search these images:
        skip_icons = [
        ]

        # find all image-files in a directory, type svg or png
        icon_path = pathlib.Path(os.path.join(docs_path, 'images'))

        image_files = [str(file) for file in icon_path.rglob('*.svg')]

        image_files += [str(file) for file in icon_path.rglob('*.png')]

        image_files = sorted(image_files,key=str.casefold)



        hit_list = {}
        for abs_path in image_files:
            file_name = os.path.basename(abs_path)
            if file_name not in skip_icons:
                search_string =  f"images/{file_name}"
                if search_string not in skip_files:
                    hit_list[abs_path] = []
                    for c_path in scan_files:
                        with open(c_path, 'r') as fp:
                            if search_string in fp.read():
                                fp.seek(0)
                                for l_no, line in enumerate(fp):
                                    if search_string in line:
                                        hit_list[abs_path].append([c_path,l_no])



        found_result = ""
        not_found_result = ""
        for abs_path in hit_list:
            trunc_abs_path = abs_path.replace(str(parent),'')

            if len(hit_list[abs_path]):
                found_path = str(hit_list[abs_path][0][0])
                rel_path = found_path.replace(str(parent),'')

                line = hit_list[abs_path][0][1]
                found_result += f"{trunc_abs_path} -> {rel_path} #{line}\n"
            else:
                not_found_result += f"{trunc_abs_path}"
                if on_load_param_1 == 'delete_unfound':
                    if os.path.isfile(abs_path):
                        try:
                            os.remove(abs_path)
                            not_found_result += " ... deleted"
                        except:
                            not_found_result += "... could not be deleted"

                not_found_result += "\n"



        print("not found:\n",not_found_result)

        print("found:\n",found_result)


    elif on_load_task == "scan_dict_usages":
        # find all usages of MY_DICT
        # construct path to SqLite-DB independent of runtime-environment
        sq3_db_file_name = 'SQLiteDict.sqlite3'
        sq3_table_name = 'snip_snippets'

        # special snippets
        skip_keys = [
        ]

        # current executed script:
        path = pathlib.Path(__file__)

        parent = path.parent.parent.absolute()

        # recursively find scan-targets: all python-files in parent.parent
        scan_files = [str(file) for file in parent.rglob('*.py')]

        print("scanned files:")
        for fc, file in enumerate(scan_files):
            print(f"   #{fc} {file}")

        sq3_db_path = os.path.join(parent, 'i18n',sq3_db_file_name)
        # ?mode=ro => read only
        uri = f'file:{sq3_db_path}'

        conn_sq3 = sqlite3.connect(uri, uri=True)
        cur_sq3 = conn_sq3.cursor()


        query_all_sq3 = f"select snip_id, snip_key from 'snip_snippets' order by snip_id asc;"

        sqlite_result = cur_sq3.execute(query_all_sq3)

        records = sqlite_result.fetchall()
        hit_list = {}
        for row in records:
            snip_id =  row[0]
            snip_key = row[1]

            if snip_key not in skip_keys:

                search_string_single_quote = f"'{snip_key}'"
                search_string_double_quote = f'"{snip_key}"'

                hit_list[snip_key] = []

                for c_path in scan_files:
                    with open(c_path, 'r') as fp:
                        file_contents = fp.read()
                        if search_string_single_quote in file_contents or search_string_double_quote in file_contents:
                            fp.seek(0)
                            for l_no, line in enumerate(fp):
                                if search_string_single_quote in line or search_string_double_quote in line:
                                    # print(c_path, scan_key,l_no,line )
                                    hit_list[snip_key].append([c_path,l_no])

        found_result = "Found snippets:\n"
        missed_usages = "Missing usage:\n"
        for snip_key in hit_list:
            if len(hit_list[snip_key]):
                abs_path = str(hit_list[snip_key][0][0])
                rel_path = abs_path.replace(str(parent),'')

                line = hit_list[snip_key][0][1]
                found_result += f"\n   {snip_key} -> {rel_path} #{line}"
            else:
                missed_usages += f"\n   {snip_key}"
                if on_load_param_1 == "delete_missing":
                    delete_missing_sq3 = f"delete from 'snip_snippets' where snip_key = \"{snip_key}\";"
                    sqlite_result = cur_sq3.execute(delete_missing_sq3)

        print(found_result)
        print(missed_usages)
        if on_load_param_1 == "delete_missing":
            print("records deleted...")
            conn_sq3.commit()



        cur_sq3.close()
        conn_sq3.close()

        # path = pathlib.Path(__file__)
        # # <class 'pathlib.PosixPath'>

        #
        # MY_DICT = SQLiteDict()
        #
        # # FeatureValidState direct assigned to error-messages

        # MY_DICT.list_usages(scan_files,skip_keys)
        pass
