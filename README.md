# Windows Service and Python Client for Process Monitoring

## Overview

This git repository provides the source code for:
- A Windows service that monitors running processes every 2 seconds. If a new process 
  starts or an existing one exits, it logs the information to a file. It also waits 
  for a client connection in parallel. As soon as a client connects, it sends the log
  file and awaits a string in return. If the string is not empty, it is the name of a
  process the service will attempt to terminate.
- A Python client whose main purpose is to demonstrate how to run a server as a
  Windows service and how to connect a client to this server to retrieve log
  information, and optionally send the name of a process to terminate.

## Motivation

The goal of this program is to limit my children's use of a specific program, and that
program alone.
