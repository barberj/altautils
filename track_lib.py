#track_lib
from random import randrange

try:
    import erp.model as m
    import erp.model.testing as tst
except ImportError:
    import portal.model as m
    import portal.model.testing as tst

testing_account = tst.Account.get(352)

def delete_track(track):
    """
    Delete tracks and their track_tests
    """
    for tracktest in track.track_tests:
        m.meta.Session.delete(tracktest)
        m.meta.Session.commit()
    m.meta.Session.delete(track)
    m.meta.Session.commit()
    return True

def create_track(method_id, count=3):
    # get the method
    method = tst.TestMethod.get(method_id)
    # create an alta track
    track = tst.Track()
    track.description = 'Alta %s' % method.short_name
    track.account = testing_account

    # get live tests we can put in the track
    tests = tst.AccountTest.query.filter_by(archived=False).\
            join(['account']).filter(tst.Account.id==testing_account.id).\
            join(['method']).filter(tst.TestMethod.id==method.id).\
            all()

    # create a track with 3 tests
    for i in range(count):
        tracktest = tst.TrackTest()
        tracktest.account = testing_account
        tracktest.track = track
        tracktest.test = tests[randrange(0,len(tests))]
        tracktest.position = i

    m.meta.Session.commit()
    return track

def create_online_track():
    return create_track(3)

def create_live_track():
    return create_track(2)

def create_irs_track(account_test_ids = [17611,17614,17590]):

    #import scoreconversion_lib as scl
    #scs = scl.track_scoreconv_set()
    irs = tst.Account.get(957)
    track = tst.Track()
    track.account = irs
    track.is_global = True
    language = ''
    #irs.conversion_set = scs

    tests = []
    for ati in account_test_ids:
        at = tst.AccountTest.get(ati)
        at.conversion_set = None
        tests.append(at)
        language = at.test.languages[0].language

    track.description = '%s Standard Progressive Battery' % language
    for i in range(len(tests)):
        print tests[i]
        tracktest = tst.TrackTest()
        tracktest.account = irs
        tracktest.track = track
        tracktest.test = tests[i]
        tracktest.position = i

    #add_track_permissions()
    m.meta.Session.commit()

    return track

def scheduletest():
    jbarber = tst.CandidateProfile.get(117680)
    test = tst.AccountTest.query.filter_by(archived=False).\
        join(['method']).filter(tst.TestMethod.id == 2).\
        join(['account']).filter(tst.Account.id == testing_account.id).\
        first()

    sct = tst.ScheduledCandidateTest()
    sct.candidate_profile = jbarber
    sct.test = test
    m.meta.Session.commit()
    sct.number = sct.id
    m.meta.Session.commit()
    sct.number = sct.id

    return sct


def add_track_permissions():
    # admin
    role = m.Role.get(19)
    role.add_permission('/portal/testing/tracks/*')
    role.add_permission('/portal/testing/track/*')

    # office
    role = m.Role.get(20)
    role.add_permission('/portal/testing/track/*')

    m.meta.Session.commit()

def create_spanish_track():
    account_test_ids = [16663,6976,12266]
    track = tst.Track()
    track.description = 'Alta Spanish'
    track.account = testing_account

    tests = []
    for ati in account_test_ids:
        at = tst.AccountTest.get(ati)
        at.archived = False
        at.conversion_set = None
        tests.append(at)

    for i in range(len(tests)):
        print tests[i]
        tracktest = tst.TrackTest()
        tracktest.account = testing_account
        tracktest.track = track
        tracktest.test = tests[i]
        tracktest.position = i

    m.meta.Session.commit()

    return track
