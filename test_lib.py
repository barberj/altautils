# test_lib.py
import logging as log
log.root.level = log.DEBUG

from sqlalchemy import and_

try:
    import erp.model as m
    import erp.model.testing as tst
    import erp.lib.altaUtils.unicode_csv as csv
except ImportError:
    import portal.model as m
    import portal.model.testing as tst
    import portal.lib.utilities.unicode_csv as csv


def change_test_html():
    item_texts = tst.TestItemVersion.query.join(['item','version','section','version','test','type']).\
        filter(and_(tst.TestItemVersion.item_text.like('%<br>%'), tst.TestType.short_name=='S')).all()
    for item in item_texts:
        log.debug('Updating %s Item %s', item.item.version.section.version.test.remarks, item.id)
        item.item_text = item.item_text.replace(u'<br><br>',u'\u000a\u000d').\
                            replace(u'<br>',u'\u000a').replace(u'<i>',u'').\
                            replace(u'</i>',u'')

