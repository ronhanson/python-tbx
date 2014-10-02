#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
"""
(c) 2013 - Ronan Delacroix
Sequential files detection lib
:author: Ronan Delacroix & Wolfgang Whoel (cinemaslides)
"""

import re
import os.path
import glob
from . import code as code_utils

class SequentialCandidate(code_utils.SerializableObject):
    """
    It creates a SequentialCandidate object which provides these attributes:
            obj.args:            List of processed strings
            obj.number_of_args
            obj.sequence:    True|False (True if at least 1 continuous numeric sequential stream is found)
            obj.composite: Composite summary of obj.args with markers for numeric sequential streams and UUIDs
            obj.ffmpeg_composite: Composite summary of obj.args with markers for numeric sequential streams and UUIDs (FFMPEG Compliant Format)
            obj.orders:        List of sequential stream directions
    """

    def __init__( self, args ):
        """
        Create the object with a list of files.
        """
        self.type = "SequentialCandidate"
        self.args = sorted(args)
        self.number_of_args = len( self.args )
        args_uuid_safe = []
        self.uuid_re = u'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        if re.search( self.uuid_re, self.args[ 0 ] ):
            args_uuid_safe = map( self._mark_uuid, self.args )
        else:
            args_uuid_safe = self.args
        self._check_sequential( args_uuid_safe )

    def _check_sequential( self, args ):
        self.composite = ''
        self.ffmpeg_composite = ''
        self.sequence = False
        self.orders = []
        splits = []
        for token in args:
            splits.append( self._numeric_and_non_numeric_particles( os.path.basename( token ) ) )
        for index in range( len( splits[ 0 ] ) ):
            column = []
            for row in splits:
                # catch dangling ends of variable-sized split lists
                if index > len( row ) - 1:
                    column.append( '' )
                else:
                    if re.match( '\d+', row[ index ] ):
                        numerical = True
                        column.append( row[ index ] )
                    else:
                        numerical = False
                        column.append( row[ index ] )
            if numerical == True:
                continuous, order, step = self._test_continuity( column )
            else:
                continuous = False
            if continuous == True:
                self.sequence = True
                self.orders.append( order )
                self.composite += '[' + str( column[ 0 ] ) + '-' + str( column[ -1 ] ) + ']'
                self.ffmpeg_composite += "%%0.%sd" % str(len(str( column[ -1 ] )))
            else:
                if len( list( set( column ) ) ) == 1:
                    self.composite += str( column[ 0 ] )
                    self.ffmpeg_composite += str( column[ 0 ] )
                else:
                    self.composite += '[GARBLED]'
                    self.ffmpeg_composite += "*"

    def _numeric_and_non_numeric_particles( self, token ):
        splits = re.split( '(\D+)', token )
        return splits

    def _test_continuity( self, sequence ):
        continuous = False
        continuity_broken = False
        order = ''
        step = 0
        try:
            initial_step = int( sequence[ 1 ] ) - int( sequence[ 0 ] )
        except:
            return False, 'None', 0
        for index, element in enumerate( sequence ):
            if index == len( sequence ) - 1:
                break
            else:
                step = int( sequence[ index + 1 ] ) - int( sequence[ index ] )
                if step == 0:
                    break
                elif step == initial_step:
                    continue
                elif step != initial_step:
                    continuity_broken = True
                    break
        if ( step != 0 and continuity_broken == False ):
            continuous = True
            if step > 0:
                order = 'ascending by ' + str( step )
            else:
                order = 'descending by ' + str( step )
        return continuous, order, step

    def _mark_uuid( self, string ):
        return re.sub( self.uuid_re, '[UUID]', string )

    def __str__(self):
        return self.composite


class SequentialFolder(SequentialCandidate):
    def __init__( self, folder_path ):
        self.folder_path = folder_path.rstrip('*').rstrip('/').rstrip('\\')
        args = glob.glob( os.path.join( self.folder_path, '*' ) )
        args = [os.path.join(self.folder_path, arg) for arg in args]
        SequentialCandidate.__init__( self, args )
        self.type = "SequentialFolder"


