# test_lib.py
import logging as log
log.root.level = log.DEBUG

from sqlalchemy import and_, or_, distinct, asc

try:
    import erp.model as m
    import erp.model.testing as tst
    import erp.lib.altaUtils.unicode_csv as csv
    from erp.model.lib.history import set_history
except ImportError:
    import portal.model as m
    import portal.model.testing as tst
    import portal.lib.utilities.unicode_csv as csv
    from portal.model.lib.history import set_history


def change_test_html():
    item_texts = tst.TestItemVersion.query.join(['item','version','section','version','test','type']).\
        filter(and_(tst.TestItemVersion.item_text.like('%<br>%'),
               or_(tst.TestType.short_name=='S', tst.TestType.short_name=='I'))).all()
    for item in item_texts:
        log.debug('Updating %s Item %s', item.item.version.section.version.test.remarks, item.id)
        item.item_text = item.item_text.replace(u'<br><br>',u'\u000a\u000d').\
                            replace(u'<br>',u'\u000a').replace(u'<i>',u'').\
                            replace(u'</i>',u'')

def update_previous(test_version_id):
    """
    fog1477

    Some online tests don't have
    the has_previous attribute set correctly.

    Given a version update the has_previous.
    """

    # get our version
    test_version = tst.TestVersion.get(test_version_id)

    previous_section_timed = False
    for section in test_version.sections:
        # The very first section never has a previous,
        # ignore archived sections,
        # don't allow users to go back to sections that aren't
        # timed inevitably stopping the clock
        if section.position > 1 and not section.archived and \
            previous_section_timed and not section.has_previous:
            section.has_previous = True
            set_history(section)
            log.debug('adding previous flag to Section %s Position %s', section.id, section.position)

        # update our timed flag for current section
        previous_section_timed = section.timed

def update_previous_all_versions():
    """
    Till we programatically fix the back button in the portal
    I'm updating all versions to have previous based on the logic
    in update_previous.
    """

    # get all the ids
    version_ids = m.meta.Session.query(distinct(tst.TestVersion.id)).filter_by(archived=False).\
        join('methods').filter_by(short_name='Online').\
        join('test','type').filter_by(short_name='RC').all()

    for version_id in version_ids:
        update_previous(version_id)
