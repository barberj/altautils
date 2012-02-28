#candidatetest_lib.py
"""
Library with functions used with CandidateTests
"""

import logging as log
log.root.level = log.DEBUG

import cStringIO

try:
    import erp.model as m
    import erp.model.testing as tst
    import erp.lib.altaUtils.unicode_csv as csv
except ImportError:
    import portal.model as m
    import portal.model.testing as tst
    import portal.lib.utilities.unicode_csv as csv


def write_excel(file_name, rows):
    buffer = cStringIO.StringIO()
    writer = csv.UnicodeWriter(buffer, dialect='excel')
    writer.writerows(rows)
    with open(file_name, 'w') as f:
        f.write(buffer.getvalue())

def grade(candidate_test, ace=True):
    # create result set
    log.debug('[%s] Creating ResultSet', candidate_test.number)
    result_set = tst.ResultSet()
    result_set.candidate_test = candidate_test
    result_set.is_final = True

    test_object = candidate_test.get_test_object()
    for scsc in test_object.score_card.score_cards_score_categories:

        level = -1 if ace else 0
        scorelevel = scsc.category.scale.levels[level]

        result = tst.ManualResult(category=scsc.category,
            level=scorelevel,result_set=result_set)

        log.debug('[%s] Creating Result %s %s',
                candidate_test.number, result.category.name,
                result.level.name)
        m.meta.Session.commit()

    #apply the conversions, if necessary
    conversion_set = candidate_test.get_conversion_set()
    if conversion_set:
        log.debug('Updating conversion')
        conversion_set.apply_conversions(result_set)

    return result_set

def get_responses(candidate_test):
    """
    Show the responses for the candidate test
    """
    from collections import namedtuple
    nt = namedtuple('CandidateTestResponse','Number, Correct, Given')

    responses = []
    for section in candidate_test.sections:
        for item in section.items:
            if item.item.type.has_response:
                responses.append(nt(item.get_number(),
                    item.version.answer, item.response))
                log.debug('%s: %s %s', item.get_number(),
                    item.version.answer, item.response)
    return responses

def create_online_test_report(candidate_test):
    """
    For online test create a report
    with the question, the correct answer (if its online),
    and the answer provided by the candidate.
    """

    report = []
    if candidate_test.test.method.short_name != 'Online':
        log.info("[%s] Not an online test, can't generate report",
            candidate_test.number)
        return report


    log.debug("[%s] Generating report for online test",
        candidate_test.number)

    result_set = candidate_test.get_final_result_set()

    header = ['TestID', 'Office', 'Candidate', 'ID', 'Test', 'TestDate',
                'TimeTaken']

    report.append(header)

    # create the base row
    header_row = [candidate_test.number,
           candidate_test.office.name if candidate_test.office else '',
           candidate_test.candidate_profile.candidate.display_as,
           candidate_test.candidate_profile.employee_id or '',
           candidate_test.test.description,
           candidate_test.local_date,
           candidate_test.duration]
    report.append(header_row)

    # if its a writing test there isn't a correct answer
    # stored in the data
    header_row = ['Section', 'Item', 'Question', 'Answer']
    writing = (candidate_test.test.test.type == tst.TestType.get(10))
    if not writing:
        header_row += ['Correct Answer']
    report.append(header_row)

    for section in candidate_test.sections:
        section_row = [section.get_name()]
        for item in section.items:

            # if it doesn't have a response its an instruction or
            # something similar that the report doesn't need
            if item.item.type.has_response:

                question = item.version.item_text or ''
                answer = None
                response = item.response

                if result_set:
                    results = item.get_results(result_set)
                    answer = (results[0].reference if results else None) or item.version.answer
                    if answer != item.response:
                        for choice in item.version.choices:
                           if choice.choice == answer:
                                answer += ' %s' % choice.choice_text

                           if choice.choice == item.response:
                                response += ' %s' % choice.choice_text


                item_row = section_row[:] + [item.get_number(), question, response or '']
                if not writing:
                    item_row += [answer or '']

                report.append(item_row)

    return report

def change_account_on_ct(test_number,account_number):
    """
    fog1046
    """

    if not test_number or not account_number:
        raise Exception('Either the required test_number or account_number are missing')

    test = tst.CandidateTest.get(test_number)
    new_account = m.Account.get(account_number)
    candidate_profile = None

    if not test or not new_account:
        raise Exception('Unable to get objects for changing the candidate test account')

    candidate = test.candidate_profile.candidate
    new_testing_account = new_account.testing_account

    # ensure candidate has profile for this account
    # if not we need to add it
    accounts = [profile.account for profile in candidate.candidate_profiles]
    if not new_testing_account in accounts:
        candidate_profile = tst.CandidateProfile()
        candidate_profile.candidate = candidate
        candidate_profile.account = new_testing_account

    # if we didn't add a profile we haven't got a variable
    # point to it yet
    if not candidate_profile:
        for profile in candidate.candidate_profiles:
            if profile.account == new_testing_account:
                candidate_profile = profile
                break

    # do the move
    credited = test.credit()

    # any office on the test
    # would be associated with the old account
    if test.office:
        test.office = None

    test.candidate_profile = candidate_profile

    # bill the test
    if credited:
        log.debug('[%s] We were able to credit!', test.number)
        test.post()
    else:
        # the test wasn't credited, probably because billing was already ran.
        # have to do some manual stuff
        # log.warning('Test account has been updated. Not able to handle the billing. Do manually')
        to_delete = []
        credit = test.posted_test_credit
        for charge in credit.charges:
            if test in charge.candidate_tests:
                #remove the test
                log.debug('charge quantity is %s', charge.quantity)
                charge.quantity -= 1
                charge.posted_quantity -= 1
                log.debug('charge quantity is %s', charge.quantity)
                sale = charge.sale
                for li in sale.line_items:
                    if li.description == charge.description:
                        log.debug('subtracting test unit %s', li.quantity)
                        li.quantity -= 1
                        log.debug('test unit %s', li.quantity)
                        log.debug('sale amount %s', sale.amount)
                        sale.amount += li.unit_rate
                        log.debug('sale amount %s', sale.amount)
                    if li.quantity == 0:
                        log.debug('quantity is zero')
                        to_delete.append(li)
                if charge.quantity == 0:
                    log.debug('charge quantity is zero')
                    charge.sale = None
                    charge.candidate_tests = []
                    to_delete.append(charge)
                old_charge = charge
                break

        new_credit = None
        for credit in new_testing_account.credit_set.credits:
            if test.posted_test_credit.type == credit.type:
                new_credit == credit
                break

        new_charge = None
        if new_credit:
            for charge in new_credit.charges:
                if old_charge.date == charge.date and \
                    old_charge.type == charge.type and \
                    old_charge.method == charge.method:
                    new_charge = charge
                    new_sale = charge.sale
                    new_charge.quantity += 1
                    new_charge.posted_quantity += 1
                    for li in new_sale.line_items:
                        if li.description == charge.description:
                            log.debug('adding a unit')
                            log.debug('test unit %s', li.quantity)
                            li.quantity += 1
                            log.debug('test unit %s', li.quantity)
                            sale.amount -= li.unit_rate
                else:
                    # to do
                    print 'No matching charge'
                    pass
        else:
            # to do
            print 'No matching credit'
            pass

    m.meta.Session.commit()
    for object in to_delete:
        log.debug('Deleting %s %s', object.id, object.__class__)
        m.meta.Session.delete(object)

    # return the test
    return test
