#evaluatorrate_lib.py

import logging as log
log.root.level = log.DEBUG

import datetime
from paste.deploy.converters import asbool

from erp.model.testing import EvaluatorRate
import erp.model as m

def fixdate(date2fix):
    if len(str(abs(date2fix.year))) <= 2:
        # we have a 2 digit year
        if date2fix.year < 20:
            # company wasn't around in the 1910s, 1920s so those must be in 21st century
            return datetime.date(2000+date2fix.year, date2fix.month, date2fix.day)
        else:
            # we have a 2 digit year should be 19xx
            return datetime.date(1900+date2fix.year, date2fix.month, date2fix.day)
    elif len(str(abs(date2fix.year))) == 4:
        # we have a 4 digit year, but its wrong century... 1910
        # company started ~1980
        if date2fix.year < 1980:
            return datetime.date(100+date2fix.year, date2fix.month, date2fix.day)
        return date2fix
    else:
        # do nothing
        return date2fix

def get_evaluator_from_cost(cost):

    contacts = cost.account.contacts
    if len(contacts) > 1:
        raise Exception("Unable to get evaluator b/c there is more then one contact tied to the Cost account")

    return contacts[0].service_provider.evaluator 

def total_cost_tests(cost):
    """
    Total up cost amount based on the tests attached to the cost
    """

    import erp.lib.evaluator_payroll as ep

    total_cost = 0
    for cte in cost.tests:
        account_test = cte.candidate_test.test
        languages = [l for l in account_test.test.languages if l.evaluator_count > 0]
        rate = ep.get_evaluator_rate(cte.evaluator, account_test.method, 
                    account_test.test.type, languages, cte.candidate_test.local_date, 
                    asbool(cte.is_review))

        total_cost += rate.rate if rate else 0 
    return total_cost


def total_cost_test_line_items(cost):
    """
    Cost amounts will include items other then tests.
    Go through the line items and total up the test amounts.
    """

    test_cost = 0 

    if cost.tests:
        for line_item in cost.line_items:
            # Exclude Test Development line items
            if 'test' in line_item.description.lower() and \
                not 'development' in line_item.description.lower():
                test_cost += line_item.amount

    return test_cost

def fog976b():
    """
    Bug with evaluators rates. If the is_review flag was none, it was returning the 
    review rate. Appropriate behavior should be to assume is_review is false.

    Code has been updated, but need to verify all the costs for that date so we can cut
    checks for the difference.
    """

    # get the costs for 11-15-2011
    nov_costs = m.Cost.query.filter_by(date=datetime.date(2011,11,15)).all()

    # for each cost
    for cost in nov_costs:
        # find total amount for the tests based on rates.
        # compare total amount to the cost amount
        # log difference
        test_cost = total_cost_tests(cost)
        test_line_item_cost = total_cost_test_line_items(cost)
        if test_cost - test_line_item_cost != 0:
            log.info('%s is owed %s\n' % (cost.account.contacts[0].full_name, test_cost - test_line_item_cost))

def fog976a():
    """
    Need to update the dates in the evaluator rates
    to 4 digits. 2 digits is defaulting to 19... 1910 != 2010
    """

    # count number of fixes
    fixed = 0

    # get all the rates
    rates = EvaluatorRate.query.all()

    log.debug('Found %s rates', len(rates))
    for rate in rates:
        new_start, new_end = None, None
        old_start = rate.start_date
        old_end = rate.end_date

        # if dates are none don't do anything
        if old_start:
            new_start = fixdate(old_start)
        
        if old_end:
            new_end = fixdate(old_end)

        # if either date is different from orig
        # make a database update
        if new_start != old_start or new_end != old_end:
            rate.start_date = new_start
            rate.end_date = new_end
            m.meta.Session.commit()
            fixed+=1
            log.info('[%s] Updated %s %s to %s %s' % (rate.id, old_start or '', old_end or '', new_start or '', new_end or ''))

    log.info('Fixed %s/%s rates', fixed, len(rates))
