#!/bin/bash
res=`echo $1| sed "s/_/\n/g"`;
port=($res)
printf '{\n'
printf '\t"data":[\n'
for key in ${!port[@]}
do
 if [[ "${#port[@]}" -gt 1 && "${key}" -ne "$((${#port[@]}-1))" ]];
then
     printf '\t {\n'
     printf "\t\t\t\"{#MYSQLPORT}\":\"${port[${key}]}\"},\n"
else [[ "${key}" -eq "((${#port[@]}-1))" ]]
     printf '\t {\n'
     printf "\t\t\t\"{#MYSQLPORT}\":\"${port[${key}]}\"}\n"
fi
done
printf '\t ]\n'
printf '}\n'