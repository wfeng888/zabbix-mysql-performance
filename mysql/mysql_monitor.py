#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import codecs
import json
#import logging
import subprocess
import sys
import types
#from logging.handlers import TimedRotatingFileHandler
#from os import path

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
PY34 = sys.version_info[0:2] >= (3, 4)


#
# CURRENT_DIR = path.abspath(path.dirname(__file__))
# logger = logging.getLogger()
# # logging.basicConfig()
# filehandler = TimedRotatingFileHandler(path.join(path.split(__file__)[0],'running.log'),when='D',backupCount=7,encoding='utf-8')
# lformat = logging.Formatter(fmt=' %(asctime)s-%(levelname)s-%(name)s-%(thread)d-%(message)s')
# filehandler.setFormatter(lformat)
# logger.addHandler(filehandler)
# #logger.setLevel(logging.INFO)
# LOG_LEVEL='DEBUG'
# logging.getLogger().setLevel(logging._nameToLevel[LOG_LEVEL])
#
# logger = logging.getLogger(__file__)

TEST=True

_mysql_software_path = '/usr/local/mysql/mysql-8.0.22-el7-x86_64/bin/mysql'
SQL_GET_VARIABLE="(SELECT variable_value from performance_schema.global_status where variable_name = '{s_variable_name}' )"
SQL_TABLE_COUNTS="select count(1) from information_schema.tables where table_schema='{s_table_schema}' and table_name ='{s_table_name}' "
SQL_TABLE_SIZE="select sum(data_length+index_length) from information_schema.tables \
where ('all'= '{s_table_schema}' and table_schema not in ('sys','information_schema','performance_schema','mysql') or table_schema='{s_table_schema}' ) \
 and ('all' = '{s_table_name}' or  table_name ='{s_table_name}' )"

if PY3:
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes

    MAXSIZE = sys.maxsize
else:
    string_types = basestring,
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str

    if sys.platform.startswith("java"):
        # Jython always uses 32 bits.
        MAXSIZE = int((1 << 31) - 1)
    else:
        # It's possible to have sizeof(long) != sizeof(Py_ssize_t).
        class X(object):

            def __len__(self):
                return 1 << 31
        try:
            len(X())
        except OverflowError:
            # 32-bit
            MAXSIZE = int((1 << 31) - 1)
        else:
            # 64-bit
            MAXSIZE = int((1 << 63) - 1)
        del X

try:
    codecs.lookup_error('surrogateescape')
    HAS_SURROGATEESCAPE = True
except LookupError:
    HAS_SURROGATEESCAPE = False

_COMPOSED_ERROR_HANDLERS = frozenset((None, 'surrogate_or_replace',
                                      'surrogate_or_strict',
                                      'surrogate_then_replace'))

def to_text(obj, encoding='utf-8', errors=None, nonstring='simplerepr'):
    """Make sure that a string is a text string

    :arg obj: An object to make sure is a text string.  In most cases this
        will be either a text string or a byte string.  However, with
        ``nonstring='simplerepr'``, this can be used as a traceback-free
        version of ``str(obj)``.
    :kwarg encoding: The encoding to use to transform from a byte string to
        a text string.  Defaults to using 'utf-8'.
    :kwarg errors: The error handler to use if the byte string is not
        decodable using the specified encoding.  Any valid `codecs error
        handler <https://docs.python.org/2/library/codecs.html#codec-base-classes>`_
        may be specified.   We support three additional error strategies
        specifically aimed at helping people to port code:

            :surrogate_or_strict: Will use surrogateescape if it is a valid
                handler, otherwise it will use strict
            :surrogate_or_replace: Will use surrogateescape if it is a valid
                handler, otherwise it will use replace.
            :surrogate_then_replace: Does the same as surrogate_or_replace but
                `was added for symmetry with the error handlers in
                :func:`ansible.module_utils._text.to_bytes` (Added in Ansible 2.3)

        Because surrogateescape was added in Python3 this usually means that
        Python3 will use `surrogateescape` and Python2 will use the fallback
        error handler. Note that the code checks for surrogateescape when the
        module is imported.  If you have a backport of `surrogateescape` for
        python2, be sure to register the error handler prior to importing this
        module.

        The default until Ansible-2.2 was `surrogate_or_replace`
        In Ansible-2.3 this defaults to `surrogate_then_replace` for symmetry
        with :func:`ansible.module_utils._text.to_bytes` .
    :kwarg nonstring: The strategy to use if a nonstring is specified in
        ``obj``.  Default is 'simplerepr'.  Valid values are:

        :simplerepr: The default.  This takes the ``str`` of the object and
            then returns the text version of that string.
        :empty: Return an empty text string
        :passthru: Return the object passed in
        :strict: Raise a :exc:`TypeError`

    :returns: Typically this returns a text string.  If a nonstring object is
        passed in this may be a different type depending on the strategy
        specified by nonstring.  This will never return a byte string.
        From Ansible-2.3 onwards, the default is `surrogate_then_replace`.

    .. version_changed:: 2.3

        Added the surrogate_then_replace error handler and made it the default error handler.
    """
    if isinstance(obj, text_type):
        return obj

    if errors in _COMPOSED_ERROR_HANDLERS:
        if HAS_SURROGATEESCAPE:
            errors = 'surrogateescape'
        elif errors == 'surrogate_or_strict':
            errors = 'strict'
        else:
            errors = 'replace'

    if isinstance(obj, binary_type):
        # Note: We don't need special handling for surrogate_then_replace
        # because all bytes will either be made into surrogates or are valid
        # to decode.
        return obj.decode(encoding, errors)

    # Note: We do these last even though we have to call to_text again on the
    # value because we're optimizing the common case
    if nonstring == 'simplerepr':
        try:
            value = str(obj)
        except UnicodeError:
            try:
                value = repr(obj)
            except UnicodeError:
                # Giving up
                return u''
    elif nonstring == 'passthru':
        return obj
    elif nonstring == 'empty':
        return u''
    elif nonstring == 'strict':
        raise TypeError('obj must be a string type')
    else:
        raise TypeError('Invalid value %s for to_text\'s nonstring parameter' % nonstring)

    return to_text(value, encoding, errors)

def _getLine(content):
    _c = to_text(content)
    if none_null_stringNone(_c):
        return None
    return _c.strip()

def _deploy_sql(port,sql):
    cmd = [_mysql_software_path, '--login-path=zabbix_'+port,'-N','-e',sql]
    #if sql:
    #    cmd +=  ' -N -e "' + ' ' + sql + '"'
    if TEST:
        print(cmd)
    try:
        return subprocess.check_output(cmd,stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        return 'errcode:%s,errmsg:%s'%(getattr(e,'returncode','1'),getattr(e,'output','error'))


def _getOutput(port,cmd='select 1;'):
    _stdout = _deploy_sql(port,sql=cmd)
    if TEST:
        print(_stdout)
    return _getLine(_stdout)

def _check_mysql_alive(port):
    res = _getOutput(port,'select 1;')
    if '1' == res :
        return True
    return False

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

def discovery(ports):
    _ports = str(ports)
    if not none_null_stringNone(_ports):
        data = [{"{#MYSQL_PORT}": _port} for _port in _ports.split('_') if ( int(_port) > 3000 and  _check_mysql_alive(_port)) ]
        print(json.dumps({"data": data}, indent=4))

def stats(port,formula):
    _operator = ('+','-','*','/','(',')')
    _tokens = ('A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z', \
               'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','_')
    _sql = 'select '
    _variable_name = ''
    for _c in formula[:]:
        if _c in _tokens:
            _variable_name += _c
        else:
            if not none_null_stringNone(_variable_name):
                _sql = _sql + ' ' + SQL_GET_VARIABLE.format(s_variable_name=_variable_name)
            if _c in _operator:
                _sql = _sql + ' ' + _c
            _variable_name = ''
    if not none_null_stringNone(_variable_name):
        _sql = _sql + ' ' + SQL_GET_VARIABLE.format(s_variable_name=_variable_name)
    _sql += ' ;'
    _res = _getOutput(port,_sql)
    print(_res)


def get_value(port,variable_name):
    _res = _getOutput(port,SQL_GET_VARIABLE.format(s_variable_name=variable_name))
    print(_res)

def check_alive(port):
    _flag = 1 if _check_mysql_alive(port) else 0
    print(_flag)

def table_counts(port,table_schema,table_name):
    _res = _getOutput(port,SQL_TABLE_COUNTS.format(s_table_schema=table_schema,s_table_name=table_name))
    print(_res)

def table_size(port,table_schema='all',table_name='all'):
    _res = _getOutput(port,SQL_TABLE_SIZE.format(s_table_schema=table_schema,s_table_name=table_name))
    print(_res)


OPERATE={
    'discovery':discovery,
    'stats':stats,
    'value':get_value,
    'alive':check_alive,
    'counts':table_counts,
    'size':table_size
}

if __name__ == '__main__':
    _operate = str(sys.argv[1])
    if _operate in OPERATE.keys():
        OPERATE[_operate](*(sys.argv[2:]))