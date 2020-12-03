#! /usr/local/bin/python3
import subprocess
import sys

CONS_SQL = "select (select gs.VARIABLE_VALUE from performance_schema.global_status gs where gs.VARIABLE_NAME = '%s')/" \
      "(select gs.VARIABLE_VALUE from performance_schema.global_status gs where gs.VARIABLE_NAME = '%s') as res from dual;"
CONS_MYSQL = '/usr/local/mysql/mysql-8.0.17-el7-x86_64/bin/mysql'
CONS_LOGIN_PATH = 'zabbix_%s'
CONS_CMD = '%s --login-path=%s -N -e \" %s \"'
CONS_PORT='3306'
if len(sys.argv) > 2:
    sql = CONS_SQL%(sys.argv[1],sys.argv[2])
    login_path = CONS_LOGIN_PATH%(CONS_PORT)
if len(sys.argv) > 3:
    login_path = CONS_LOGIN_PATH%(sys.argv[3])
cmd = CONS_CMD%(CONS_MYSQL,login_path,sql)
res = subprocess.run(cmd,capture_output=True,shell=True,encoding='utf8')
outs = res.stdout.splitlines()[0]
if outs == 'NULL':
    outs = 0
print(outs)