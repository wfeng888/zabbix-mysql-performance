#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json,requests
import os
import subprocess
import sys,pickle
from copy import deepcopy


http_host='10.45.154.78'
http_port=9200
zabbix_agent_cnf = '/etc/zabbix/zabbix_agentd.conf'
log_path = os.path.abspath('./runing.log')
data_dir = '/etc/zabbix/sender_data'
cumulate_data_file = '/etc/zabbix/sender_data/last_data'

def isNull(param):
    return not ( param and str(param).strip() )

def stringNone(param):
    return  param and str(param).upper() == 'NONE'

def none_null_stringNone(param):
    if isinstance(param,(tuple,list)):
        for i in param:
            if not (isNull(param) or stringNone(param)):
                return False
        return True
    return isNull(param) or stringNone(param)

def write_log(res=None,msg=None):
    if res:
        if res.returncode != 0:
            if not msg:
                msg = res.stderr
            else:
                msg += res.stderr
    if msg:
        with open(log_path,'w',encoding='utf-8') as f:
            f.write(msg)
            f.write('\n')

def mminus(v1,v2):
    if none_null_stringNone(v1):
        v1 = 0
    if none_null_stringNone(v2):
        v2 = 0
    return v1 - v2 if v1 >= v2 else 0

def complex_minus(v1,v2,items=()):
    for i in items:
        v1 = v1.get(i,None) if v1 else None
        v2 = v2.get(i,None) if v2 else None
    return mminus(v1,v2)


def write_index_stats(http_host,http_port,index_name,file_path):
    res = requests.get('http://{0}:{1}/{2}/_stats?filter_path=_all.primaries.*'.format(http_host,http_port,index_name))
    res_str = ''
    if os.path.exists(cumulate_data_file):
        with open(cumulate_data_file,'rb') as f:
            last_data = pickle.load(f)
    else:
        subprocess.run('touch %s'%cumulate_data_file,shell=True)
        last_data = {}
    # if not isinstance(cumulate_data,dict):
    #     cumulate_data = {}
    this_data = {}
    if res.status_code == 200:
        stats_data = res.json()['_all']['primaries']
        this_data[index_name] = deepcopy(stats_data)
        with open(cumulate_data_file,'wb') as f:
            pickle.dump(this_data,f)
        last_data = last_data.get(index_name,None)
        res_str += '- %s.store.size_in_bytes_ps  %d\n'%(index_name,complex_minus(stats_data,last_data,('store','size_in_bytes')))
        res_str += '- %s.indexing.index_total_ps  %d\n'%(index_name,complex_minus(stats_data,last_data,('indexing','index_total')))
        res_str += '- %s.merges.current  %d\n'%(index_name,stats_data['merges']['current'])
        res_str += '- %s.merges.current_size_in_bytes  %d\n'%(index_name,stats_data['merges']['current_size_in_bytes'])
        res_str += '- %s.merges.total  %d\n'%(index_name,stats_data['merges']['total'])
        res_str += '- %s.merges.total_ps  %d\n'%(index_name,complex_minus(stats_data,last_data,('merges','total')))
        res_str += '- %s.refresh.total  %d\n'%(index_name,stats_data['refresh']['total'])
        res_str += '- %s.refresh.total_ps  %d\n'%(index_name,complex_minus(stats_data,last_data,('refresh','total')))
        res_str += '- %s.flush.total  %d\n'%(index_name,stats_data['flush']['total'])
        res_str += '- %s.flush.total_ps  %d\n'%(index_name,complex_minus(stats_data,last_data,('flush','total')))
        res_str += '- %s.flush.total_time_in_millis  %d\n'%(index_name,stats_data['flush']['total_time_in_millis'])
        res_str += '- %s.warmer.total  %d\n'%(index_name,stats_data['warmer']['total'])
        res_str += '- %s.warmer.current  %d\n'%(index_name,stats_data['warmer']['current'])
        res_str += '- %s.segments.count  %d\n'%(index_name,stats_data['segments']['count'])
        # res_str += '- %s.segments.count_ps  %d\n'%(index_name,complex_minus(stats_data,last_data,('segments','count')))
        res_str += '- %s.segments.memory_in_bytes  %d\n'%(index_name,stats_data['segments']['memory_in_bytes'])
        # res_str += '- %s.segments.memory_in_bytes_ps  %d\n'%(index_name,complex_minus(stats_data,last_data,('segments','memory_in_bytes')))
        res_str += '- %s.segments.index_writer_memory_in_bytes  %d\n'%(index_name,stats_data['segments']['index_writer_memory_in_bytes'])
        # res_str += '- %s.segments.index_writer_memory_in_bytes_ps  %d\n'%(index_name,complex_minus(stats_data,last_data,('segments','index_writer_memory_in_bytes')))
        # res_str += '- %s.segments.file_sizes  %d\n'%(index_name,stats_data['segments']['file_sizes'])
        res_str += '- %s.translog.size_in_bytes  %d\n'%(index_name,stats_data['translog']['size_in_bytes'])
        res_str += '- %s.translog.size_in_bytes_ps  %d\n'%(index_name,complex_minus(stats_data,last_data,('translog','size_in_bytes')))
        # res_str += '- %s.translog.operations  %d\n'%(index_name,stats_data['translog']['operations'])
        res_str += '- %s.translog.operations_ps  %d\n'%(index_name,complex_minus(stats_data,last_data,('translog','operations')))
        with open(file_path,'w',encoding='utf-8') as f:
            f.write(res_str)


def send_data(file_path):
    cmd = '/usr/bin/zabbix_sender -c %s -i %s '%(zabbix_agent_cnf,file_path)
    res = subprocess.run(cmd,capture_output=True,shell=True,encoding='utf8')
    write_log(res)


if __name__ == '__main__':
    index_name = sys.argv[1]
    cmd = 'mkdir -p %s'%data_dir
    res = subprocess.run(cmd,capture_output=True,shell=True,encoding='utf-8')
    write_log(res)
    write_index_stats(http_host,http_port,index_name,os.path.join(data_dir,index_name))
    send_data(os.path.join(data_dir,index_name))
