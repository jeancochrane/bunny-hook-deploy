#!/bin/bash

service nginx reload
service nginx restart
supervisorctl update bunny-hook
