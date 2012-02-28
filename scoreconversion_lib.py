#scoreconversion_lib.py
"""
Library with functions used to manipulate ScoreConversionSets and ScoreConversion objects
"""

import logging as log
log.root.level = log.DEBUG

import sys
import datetime
from sqlalchemy import and_

try:
    import erp.model.testing as tst
except ImportError:
    import portal.model.testing as tst

now = datetime.datetime.now()

def getILR(level):
    """
    Given an ALTA Level value return
    corresponding ILR value

    if level < 5:
        return '0+' if level == 4 else '0'

    if level < 7:
        return '1+' if level == 6 else '1'

    if level < 9:
        return '2+' if level == 8 else '2'

    if level < 11:
        return '3+' if level == 10 else '3'

    if level < 13:
        return '4+' if level == 12 else '4'
    """

    # exclusive ceiling for the grade
    # ie if you got an ALTA level of 4
    # you would be in the first cut off
    grade_cut_off = 5

    # we are going to iterate through the ILR levels
    # IRL 0,0+,1,1+,....4,4+,5
    for i in range(5):
        # if level is less the cut off, then we need to return our value
        if level < grade_cut_off:
            # 1 less then cut off is ILR+ level
            return str(i) + '+' if level == (grade_cut_off - 1) else str(i)
        grade_cut_off += 2

    return '5'

def track_scoreconv_set():
    scs = tst.ScoreConversionSet()
    scs.created_at = now
    scs.updated_at = now
    scs.name = 'IRS Pass 64%/3'
    scs.has_ilr = True
    scs.ilr_only = False

    # percentages
    scs.conversions.append(create_conversion('Fail',0,True,64,False,True))
    scs.conversions.append(create_conversion('Pass',64,True,100,True,True))

    # ilr
    scs.conversions.append(create_conversion('Fail',0,True,9,False))
    scs.conversions.append(create_conversion('Pass',9,True,13,False))
    # return the new scoreconversionset

    scs = tst.ScoreConversionSet()
    scs.created_at = now
    scs.updated_at = now
    scs.name = 'IRS Pass 70%/3'
    scs.has_ilr = True
    scs.ilr_only = False

    # percentages
    scs.conversions.append(create_conversion('Fail',0,True,70,False,True))
    scs.conversions.append(create_conversion('Pass',70,True,100,True,True))

    # ilr
    scs.conversions.append(create_conversion('Fail',0,True,9,False))
    scs.conversions.append(create_conversion('Pass',9,True,13,False))
    # return the new scoreconversionset

    return scs

def fog1023():
    scs = tst.ScoreConversionSet()
    scs.created_at = now
    scs.updated_at = now
    scs.name = 'Reading Test ILR 2+/3+'
    scs.has_ilr = True
    scs.ilr_only = False

    scs.conversions.append(create_conversion('Below ILR 2+',0,True,28,False,True))
    scs.conversions.append(create_conversion('ILR 2+',28,True,64,False,True))
    scs.conversions.append(create_conversion('ILR 3',64,True,84,False,True))
    scs.conversions.append(create_conversion('ILR 3+',84,True,100,True,True))
    # return the new scoreconversionset
    return scs


def fog996():
    # create a new Pass/Fail ILR conversion set
    # going to copy the one created in fog941
    # and update the converted value
    scs = tst.ScoreConversionSet()
    scs.created_at = now
    scs.updated_at = now
    scs.name = 'Pass (ILR 3)'
    scs.has_ilr = True
    scs.ilr_only = False

    for level in range(14):
        converted_value = 'Did Not Pass (ILR %s)' if level < 9 else 'Pass (ILR %s)'
        converted_value = converted_value % getILR(level)
        scs.conversions.append(create_conversion(converted_value,level))
    # return the new scoreconversionset
    return scs

def fog941():
    # Create a new Pass/Fail conversion set
    scs = tst.ScoreConversionSet()
    scs.created_at = now
    scs.updated_at = now
    scs.name = 'Pass (10)'
    scs.has_ilr = True
    scs.ilr_only = False

    # Create the Conversions for the set
    # Banfield has the default values we want
    scs_to_copy = tst.ScoreConversionSet.get(23)
    for conversion in scs_to_copy.conversions:
        if not conversion.archived:
            scs.conversions.append(copy_conversion(conversion))
    # return the new scoreconversionset
    return scs

def create_conversion(converted_value,min_value,min_inclusive=True, max_value=-1, max_inclusive=True, use_percentages=False):
    # create conversion with defaults
    # defaults are traditaional conversion
    # where min = max and there are 13 levels
    # if max_value = -1 then use min

    if max_value == -1:
        max_value = min_value

    return tst.ScoreConversion(converted_value=converted_value,
        min_value=min_value,
        min_inclusive=min_inclusive,
        max_value=max_value,
        max_inclusive=max_inclusive,
        use_percentages=use_percentages,
        created_at=now,
        updated_at=now)

def copy_conversion(conversion_to_copy):
    return tst.ScoreConversion(converted_value=conversion_to_copy.converted_value,
        min_value=conversion_to_copy.min_value,
        min_inclusive=conversion_to_copy.min_inclusive,
        max_value=conversion_to_copy.max_value,
        max_inclusive=conversion_to_copy.max_inclusive,
        use_percentages=conversion_to_copy.use_percentages,
        created_at=now,
        updated_at=now)

def convert_conversion(conversion_to_convert,converted_value):
    conversion.archived = True
    conversion.updated_at = now
    return tst.ScoreConversion(converted_value=converted_value,
        min_value=conversion.min_value,
        min_inclusive=conversion.min_inclusive,
        max_value=conversion.max_value,
        max_inclusive=conversion.max_inclusive,
        use_percentages=conversion.use_percentages,
        created_at=now,
        updated_at=now)

def print_active_conversions(scs):
    scs.conversions.sort(key=lambda conversion : conversion.min_value)
    print scs.name, scs.has_ilr, scs.ilr_only, scs.has_ilr, scs.ilr_only
    for conversion in scs.conversions:
        if not conversion.archived:
            print conversion.converted_value, conversion.min_value, conversion.min_inclusive, conversion.max_value, conversion.max_inclusive, conversion.use_percentages

def find_missing_values(cs):
    """
    Iterator through Conversions and verify there are min_values for 0-13
    """
    try:
        active_conversions = [conversion for conversion in cs.conversions if not conversion.archived]
        active_conversions.sort(key=lambda conversion : conversion.min_value)

        #pull out values
        values = [conversion.min_value for conversion in active_conversions]
        for i in range(14):
            if i not in values:
                print 'Missing value %s' % i
    except Exception, ex:
        print ex

def fix_conversionset(cs):
    new_conversions = []
    for conversion in cs.conversions:
        if not conversion.archived:

            if conversion.min_value == conversion.max_value == 2 and '0+' in conversion.converted_value:
                new_conversions.append(convert_conversion(conversion,conversion.converted_value.replace('0+','0')))

            elif conversion.min_value == conversion.max_value == 3 and '0+' in conversion.converted_value:
                new_conversions.append(convert_conversion(conversion,conversion.converted_value.replace('0+','0')))

            elif conversion.min_value == conversion.max_value == 4 and '1' in conversion.converted_value:
                new_conversions.append(convert_conversion(conversion,conversion.converted_value.replace('1','0+')))

            elif conversion.min_value == conversion.max_value == 5 and '1+' in conversion.converted_value:
                new_conversions.append(convert_conversion(conversion,conversion.converted_value.replace('1+','1')))

            elif conversion.min_value == conversion.max_value == 6 and '2' in conversion.converted_value:
                new_conversions.append(convert_conversion(conversion,conversion.converted_value.replace('2','1+')))

            elif conversion.min_value == conversion.max_value == 10 and '4' in conversion.converted_value:
                new_conversions.append(convert_conversion(conversion,conversion.converted_value.replace('4','3+')))

            elif conversion.min_value == conversion.max_value == 11 and '4+' in conversion.converted_value:
                new_conversions.append(convert_conversion(conversion,conversion.converted_value.replace('4+','4')))

            elif conversion.min_value == conversion.max_value == 12 and '5' in conversion.converted_value:
                new_conversions.append(convert_conversion(conversion,conversion.converted_value.replace('5','4+')))

    cs.conversions += new_conversions

def get_gls_ilr_conversions():
    scs = tst.ScoreConversionSet.query.filter(and_(tst.ScoreConversionSet.id!=76, tst.ScoreConversionSet.archived==False)).all()
    gls = []
    for cs in scs:
        for conversion in cs.conversions:
            if not conversion.archived:
                if 'gls' in conversion.converted_value.lower():
                    gls.append(cs)
    return gls

def archive_scoreconversionset(cs):
    """
    Archive the ScoreConversionSet and its conversions
    """
    for conversion in cs.conversions:
        if not conversion.archived:
            conversion.archived = True
    cs.archived = True
    return cs

def get_scs():
    return tst.ScoreConversionSet.query.filter(tst.ScoreConversionSet.archived==False).all()

def fog746():
    scs = tst.ScoreConversionSet.query.filter(and_(tst.ScoreConversionSet.id!=76, tst.ScoreConversionSet.archived==False)).all()
    ilr = []
    for cs in scs:
        for conversion in cs.conversions:
            if not conversion.archived:
                if 'ilr' in conversion.converted_value.lower():
                    ilr.append(cs)
    ilr = list(set(ilr))
    print "There are %s ConversionsSets" % len(ilr)
    for cs in ilr:
        print cs.name, cs.id
        cs.conversions.sort(key=lambda conversion : conversion.min_value)
        for conversion in cs.conversions:
            if not conversion.archived:
                pass
                #print conversion.converted_value, conversion.min_value, conversion.min_inclusive, conversion.max_value, conversion.max_inclusive, conversion.use_percentages
    sys.exit(0)

    for cs in ilr:
        new_conversions = []
        for conversion in cs.conversions:
            if not conversion.archived:
                if conversion.min_value == conversion.max_value == 2 and '0+' in conversion.converted_value:
                    new_conversions.append(convert_conversion(conversion,conversion.converted_value.replace('0+','0')))
                elif conversion.min_value == conversion.max_value == 3 and '0+' in conversion.converted_value:
                    new_conversions.append(convert_conversion(conversion,conversion.converted_value.replace('0+','0')))
                elif conversion.min_value == conversion.max_value == 4 and '1' in conversion.converted_value:
                    new_conversions.append(convert_conversion(conversion,conversion.converted_value.replace('1','0+')))
                elif conversion.min_value == conversion.max_value == 5 and '1+' in conversion.converted_value:
                    new_conversions.append(convert_conversion(conversion,conversion.converted_value.replace('1+','1')))
                elif conversion.min_value == conversion.max_value == 6 and '2' in conversion.converted_value:
                    new_conversions.append(convert_conversion(conversion,conversion.converted_value.replace('2','1+')))
                elif conversion.min_value == conversion.max_value == 10 and '4' in conversion.converted_value:
                    new_conversions.append(convert_conversion(conversion,conversion.converted_value.replace('4','3+')))
                elif conversion.min_value == conversion.max_value == 11 and '4+' in conversion.converted_value:
                    new_conversions.append(convert_conversion(conversion,conversion.converted_value.replace('4+','4')))
                elif conversion.min_value == conversion.max_value == 12 and '5' in conversion.converted_value:
                    new_conversions.append(convert_conversion(conversion,conversion.converted_value.replace('5','4+')))
        cs.conversions += new_conversions
        find_missing_values(cs)
        print_active_conversions(cs)
