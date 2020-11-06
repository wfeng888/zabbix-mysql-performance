#
sudo -u zabbix  echo "show global status where Variable_name='Aborted_clients'; " | /usr/local/mysql/mysql-8.0.22-el7-x86_64/bin/mysql --login-path=mysql_3309_zabbix  -N  | awk '{print $2}' 

zabbix_get -s 10.45.156.202 -k "mysql.status2[group_replication_primary_member,3309]"