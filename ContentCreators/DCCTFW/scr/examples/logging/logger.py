

'''
the logger is initialized when Maya open. It uses the standard python logging library which is set up in scr.__init__

mapping for logger severity
not set = 0
debug = 10
info = 20
warning = 30
error = 40
critical = 50
'''


'''
import logging and scr
'''
import logging
import scr

'''
get the logger which was already initialized
'''
logger = logging.getLogger(scr.logger_name)

'''
get current level...10 maps to Debug
'''
# get current level
scr.get_logger_level()
# Result: 10

'''
in module send a debug message through the logger
'''
logger.debug('Debug message!')
# 01-07-2024 16:38:37 - DEBUG - line number: 2 - <maya console> - Debug message!
# DCCF : Debug message!

'''
change level to 50...Critical
'''
scr.set_logger_level(50)

'''
throw crutical message
'''
logger.critical('Critical message')
# 01-07-2024 16:51:29 - CRITICAL - line number: 2 - <maya console> - Critical message
# Error: DCCF : Critical message


'''
in a try
'''
try:
    1/0
except Exception as argument:
    logger.error(argument)
# 01-07-2024 17:08:36 - ERROR - line number: 5 - <maya console> - division by zero
# Error: DCCF : division by zero

'''
look at all the logger currently running in Maya
'''
scr.get_all_loggers_by_name()
#...
# log name :: setuptools.config
# log name :: setuptools.config.pyprojecttoml
# log name :: concurrent.futures
# log name :: concurrent
# log name :: asyncio
# log name :: future_stdlib
# log name :: DCCF
# log name :: mtoa.txManager.lib
# log name :: mtoa.txManager
#...