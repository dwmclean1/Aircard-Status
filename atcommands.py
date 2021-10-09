# AT Commands
MAKE = 'at+cgmi'
MODEL = 'at+cgmm'
STATUS = 'at!gstatus?'
BANDMASK = 'at!gband?'
SIGNALQ = 'at+csq'
PWRMODE = { 'reboot': 'at!reset',
            'lowpower': 'at+cfun=4',
            'fullpower': 'at+cfun=1'}

