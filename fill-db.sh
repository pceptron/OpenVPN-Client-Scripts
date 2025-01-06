#!/usr/bin/env bash
# Configuration of rotation netflow statistics
# More details here: https://github.com/vmxdev/xenoeye
EXP_DIR="/var/lib/xenoeye/exp"
FAIL_DIR="/var/lib/xenoeye/expfailed/"

for sqlscript in $EXP_DIR/*.sql; do
  psql postgresql://<DB_USERNAME>:<PASSWORD>@<DB_HOST>/xenoeyedb -f "$sqlscript"
  if [ $? -eq 0 ]; then
      rm -f "$sqlscript"
  else
      mv "$sqlscript" $FAIL_DIR
  fi
done

