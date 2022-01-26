"""
------------------------------------------------------------------------
Title: APP - Notes - Utility
Author: Matthew May
Date: 2017-06-13
Notes: Project Notes
Notes:
------------------------------------------------------------------------
"""
class ProcessNotes():

    # note_id = Project identifier (object)
    # user = instance of accountprofile (object)
    # change_type = project or change
    # note = the message listed against the project or change
    def __init__(note_id,user,change_type='project',note=''):