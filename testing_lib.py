# testing_lib.py

import requests
try:
    import erp.model as m
    import erp.model.testing as tst
except ImportError:
    import portal.model as m
    import portal.model.testing as tst

def fog1270():
    """
    Create an xls with active evaluators emails by language
    """
    from xlwt import Workbook
    rates = tst.EvaluatorRate.query.join('evaluator','service_provider','contact').\
                filter_by(active=True).all()
    language_dict = {}
    for rate in rates:
        language_dict.setdefault(rate.language,[]).\
    append(rate.evaluator.service_provider.contact.get_email_address())

    distro = Workbook()
    row = 0

    active = distro.add_sheet('Active Evaluators')

    for language in language_dict:
        emails = language_dict[language]
        emails = list(set(emails))
        email_str = ''
        for email in emails:
            email_str = email_str + '%s;' % email
        email_str = email_str[:-1]
        active.write(row, 0, language.name)
        active.write(row, 2, email_str)
        row+=1

    distro.save('evaluators.xls')

def tmz():
    from xlwt import Workbook
    rates = tst.EvaluatorRate.query.join('evaluator','service_provider','contact').\
                filter_by(active=True).all()
    language_dict = {}
    for rate in rates:
        language_dict.setdefault(rate.language,[]).\
    append(rate.evaluator.service_provider.contact.time_zone)

    distro = Workbook()
    row = 0

    active = distro.add_sheet('Active Evaluators')

    for language in language_dict:
        tmzs = language_dict[language]
        tmzs = list(set(tmzs))
        tmz_str = ''
        for tmz in tmzs:
            tmz_str = tmz_str + '%s;' % tmz
        tmz_str = tmz_str[:-1]
        active.write(row, 0, language.name)
        active.write(row, 2, tmz_str)
        row+=1

    distro.save('evaluators.xls')

def test_question_report(test_number):
    url = 'http://localhost:5000/testing/candidatetests/generate_question_report/Test %(test_number)s.pdf?id=%(test_number)s' % {'test_number':test_number}

    print url
    response = requests.get(url, config={'decode_unicode':False})

    print response.ok
    data = response.content

    with open('test.pdf','wb') as f:
        f.write(data)
