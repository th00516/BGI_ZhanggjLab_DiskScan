#!/usr/bin/env python
#-*- coding:utf-8 -*-


'''

    Author: Hao Yu (yuhao@genomics.cn)
    Date:   2018-11-07

    ChangeLog:
        v0.1
            2018-11-07
                Initiation
        v0.2
            2018-11-15
                To use a new data structure
        v1.0
            2018-11-15
                To add report function

'''


import sys
import os


def combine_result(input_list):
    'This function is used for combining all the separate result into one box'

    result_path_list = []

    for i in input_list:

        if os.path.isdir(i):

            for r in os.listdir(i):
                result_path_list.append(os.path.join(i, r))

        else:
            result_path_list.append(i)

    result_box = {'FD':{},'LF':{},'BL':[],'nAD':{}}

    for result_path in result_path_list:
        with open(result_path, 'rb') as fh:
            for l in fh:
                l = l.split()

                if l[0].startswith('#'):
                    continue

                record_class = l[0]

                if record_class == 'FD' or record_class == 'LF':
                    record_owner = l[1]
                    record_inode = l[2]
                    record_path = l[6]

                    record_size = l[3]
                    record_mtime = l[4]
                    record_atime = l[5]

                    if not result_box[record_class].has_key(record_owner):
                        result_box[record_class].update({record_owner:{}})

                    if not result_box[record_class][record_owner].has_key(record_inode):
                        result_box[record_class][record_owner].update({record_inode:[record_size,record_mtime,record_atime,record_path]})
                elif record_class == 'BL':
                    record_path = l[1]

                    result_box[record_class].append(record_path)
                elif record_class == 'nAD':
                    record_owner = l[1]
                    record_inode = l[2]
                    record_path = l[3]

                    if not result_box[record_class].has_key(record_owner):
                        result_box[record_class].update({record_owner:{}})

                    if not result_box[record_class][record_owner].has_key(record_inode):
                        result_box[record_class][record_owner].update({record_inode:[record_path]})
                else:
                    print >> sys.stderr, result_path + ' may be not your kind of record in disk-scanning'

    return result_box


def compare_newAndOld_results(new_result_box, old_result_box = None):
    'This function is used for comparing new and old results'

    noHandle_item_box = {}

    for record_class in new_result_box:
        if not noHandle_item_box.has_key(record_class):
            noHandle_item_box.update({record_class:{}})

        if record_class != 'BL':
            for record_owner in new_result_box[record_class]:
                if not noHandle_item_box[record_class].has_key(record_owner):
                    noHandle_item_box[record_class].update({record_owner:[]})

                for record_inode in new_result_box[record_class][record_owner]:
                    if old_result_box and \
                       old_result_box.has_key(record_class) and \
                       old_result_box[record_class].has_key(record_owner) and \
                       old_result_box[record_class][record_owner].has_key(record_inode):
                        noHandle_item_box[record_class][record_owner].append([record_class,record_owner,\
                                                                              new_result_box[record_class][record_owner][record_inode],\
                                                                              old_result_box[record_class][record_owner][record_inode],'UH'])
                    else:
                        noHandle_item_box[record_class][record_owner].append([record_class,record_owner,\
                                                                              new_result_box[record_class][record_owner][record_inode],['-'],'NR'])
        else:
            for broken_link in new_result_box[record_class]:
                if not noHandle_item_box[record_class].has_key('WARNING'):
                    noHandle_item_box[record_class].update({'WARNING':[]})

                noHandle_item_box[record_class]['WARNING'].append([record_class,'WARNING',\
                                                                  [broken_link],['-'],'WA'])

    return noHandle_item_box


def report_result(compared_result_box):
    'This function is used for plotting'

    statisticsByOwner_box = {}

    for record_class in compared_result_box:
        for record_owner in compared_result_box[record_class]:

            if not statisticsByOwner_box.has_key(record_owner):
                statisticsByOwner_box.update({record_owner:{}})

            if not statisticsByOwner_box[record_owner].has_key(record_class):
                statisticsByOwner_box[record_owner].update({record_class:{'new':0,'old':0}})

            for record in compared_result_box[record_class][record_owner]:

                new_item_size = 0
                old_item_size = 0

                if record_class == 'LF':

                    new_item_size = float(record[2][0][:-1])

                    if record[3][0] != '-':
                        old_item_size = float(record[3][0][:-1])
                    else:
                        old_item_size = 0

                elif record_class == 'FD':

                    new_item_size = int(record[2][0])

                    if record[3][0] != '-':
                        old_item_size = int(record[3][0])
                    else:
                        old_item_size = 0

                elif record_class == 'nAD':

                    new_item_size = 1

                    if record[3][0] != '-':
                        old_item_size = 1
                    else:
                        old_item_size = 0

                statisticsByOwner_box[record_owner][record_class]['new'] += new_item_size
                statisticsByOwner_box[record_owner][record_class]['old'] += old_item_size

    return statisticsByOwner_box


if __name__ == '__main__':

    fh_output = open(sys.argv[1] + '.output.txt', 'wb')
    fh_report = open(sys.argv[1] + '.report.txt', 'wb')

    try:
        if len(sys.argv) == 4:
            outbox = compare_newAndOld_results(combine_result([sys.argv[2],]), combine_result([sys.argv[3],]))
        else:
            outbox = compare_newAndOld_results(combine_result([sys.argv[2],]))

        for record_class in outbox:
            for record_owner in outbox[record_class]:
                for record in outbox[record_class][record_owner]:
                    print >> fh_output, '\t'.join([record[0], record[1], '\t'.join(record[2]), '\t'.join(record[3]), record[-1]])

        report_box = report_result(outbox)

        for report_owner in sorted(report_box.keys()):
            for report_class in sorted(report_box[report_owner].keys()):

                consumed_ration = '-'

                if report_box[report_owner][report_class]['old'] > 0:
                    consumed_ration = '%.2f' % (report_box[report_owner][report_class]['new'] / report_box[report_owner][report_class]['old'] * 100)

                if report_class == 'LF':
                    print >> fh_report, report_owner, '\t', report_class + ': ', str(report_box[report_owner][report_class]['new']) + 'G', '/', \
                                                                                 str(report_box[report_owner][report_class]['old']) + 'G', '\t', consumed_ration
                else:
                    print >> fh_report, report_owner, '\t', report_class + ': ', str(report_box[report_owner][report_class]['new']), '/', \
                                                                                 str(report_box[record_owner][record_class]['old']), '\t', consumed_ration
    except:
        print >> sys.stderr, 'USAGE:  ' + sys.argv[0] + ' <prefix> <scanning outdir> [old scanning outdir]'
