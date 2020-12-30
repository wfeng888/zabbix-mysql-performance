#!/usr/bin/python
import os
import json
import sys

if __name__ == "__main__":
    # Iterate over all block devices, but ignore them if they are in the
    # skippable set
    _disks = sys.argv[1] if len(sys.argv) > 1 else None
    _skip = False
    if _disks:
        _skip = True if _disks[0] == '-' else False
        if any(_disks[0] == _flag for _flag in ( '-', '+')):
            _disks = _disks[1:]
        _disks = _disks.split(',')
    skippable = set(["sr", "loop", "ram"])
    skippable = skippable if not _skip else skippable|set(_disks)
    if _skip:
        _disks = ()
    print(_skip)
    print(_disks)
    print(skippable)
    devices = (device for device in os.listdir("/sys/class/block")
               if not any(ignore in device for ignore in skippable) and (_skip or any(_include in device for _include in _disks)))
    data = [{"{#DEVICENAME}": device} for device in devices]
    print(json.dumps({"data": data}, indent=4))