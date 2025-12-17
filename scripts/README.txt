Helper scripts can live here if you decide you want install helpers later.
For v1, the main entrypoint is:

  python3 -m proxreport serve --config /path/to/config.ini

and user creation:

  python3 -m proxreport hash-password --username <user>
