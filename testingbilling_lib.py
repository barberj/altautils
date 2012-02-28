# testingbilling_lib.py
import logging
logging.root.level=logging.DEBUG
log = logging

import datetime
from sqlalchemy import and_

import erp.model as m
import erp.model.testing as tst
import erp.lib.testing_billing as testing_billing

import sys

def update_candidate_charges(tests,test_type_description='Writing',test_method_description='Paper Test', force=False):
    # candidates can only buy online live test credits.
    # there are occaions they need paper etc. 

    for test in tests:
        ct = tst.CandidateTest.get(test)
        if not ct:
            raise Exception('Unable to get the test needing to be posted correctly')

        ct.candidate_profile.candidate.charges.sort(key=lambda charge : charge.date)
        charge = ct.candidate_profile.candidate.charges[-1]
        credit = charge.posted_test_credit

        if not charge.balance > 0 and credit and not credit.balance > 0:
            raise Exception('Charge/Credit does not have a balance')

        if not charge.date.month == ct.created_at.month and not force:
            raise Exception('Charge and test do not match. Verify and use force to continue')


        test_method = tst.TestMethod.get_by(description=test_method_description)
        test_type = tst.TestType.get_by(description=test_type_description)

        existing_credit = tst.TestCredit.query.filter_by(candidate_profile=ct.candidate_profile).filter_by(method=test_method).filter_by(type=test_type).all()
        if existing_credit:
            if not force:
                raise Exception('Found a test credit matching criteria.')
            if force:
                # increment counts on the existing_credits balance and delete the credit tied to the charge
                pass

        if not test_method or not test_type:
            raise Exception('Unable to get the type and method to update the credit too')

        credit.method = test_method
        credit.type = test_type

        charge.method = test_method
        charge.type = test_type

         ct.post()
    m.meta.Session.commit()

        

def fog1046():
    # invoice was reissued, however the account had already paid the invoice.
    # so they want the test that was added to the invoice to be moved to 
    # the next month
    test = tst.CandidateTest.get(276789)
    if not test:
        raise Exception('Unable to get test to move')

    # using the credit we get the charge and sales
    credit = test.posted_test_credit
    original_balance = credit.balance

    for charge in test.posted_test_credit.charges:
        if test in charge.candidate_tests:
            break

    if not test in charge.candidate_tests:
        raise Exception('Charge issue')

    # update the old sale
    sale = charge.sale
    for line_item in sale.line_items:
        if test.test.test.type.description in line_item.description and \
            test.test.method.short_name in line_item.description:
            line_item.quantity -= 1
            sale.amount += line_item.unit_rate

    # remove the test from the old charge
    charge.candidate_tests.remove(test) 
    test.posted_test_credit = None
    test.billed_by = None
    test.billing_lock = False
    test.is_posted = None
    
    # posting will udpate the credit balance and make it picked up next time billing is ran
    test.post()
    print 'Credit Balance Orig %s, Updated %s' % (original_balance, credit.balance)
    return test

def fog1042():

    november = datetime.date(2011,11,30)

    sales = m.Sale.query.filter(and_(m.Sale.date==november,
                m.Sale.department==m.Department.get_by(name=u'Testing'))).all()


    log.info('Checking %s Sales', len(sales))
    errors = []
    for sale in sales:
        inv_addr = sale.address

        # to find the entity that created the sale, we 
        # need to look at the charges
        for charge in sale.charges:
            entity = charge.parent
    
            # only care about accounts and offices
            if not isinstance(entity,tst.CandidateProfile):
                address = testing_billing.get_entity_address(entity)

                # if office isn't invoice lets get account address
                if isinstance(entity, tst.Office):
                    if not entity.is_invoiced:
                        address = testing_billing.get_entity_address(entity.account)

                # simple check... i don't expect this to error
                if inv_addr != address:
                    log.warning('Sale address does not match the entity address IS%s\n%s\n%s', sale.id, inv_addr, address)
                    errors.append([sale.id, inv_addr, address])

                # now lets verify against the contact on entity
                if isinstance(entity, tst.Office):
                    try:
                        if entity.contact:
                            address = entity.contact.postal_addresses[0].full_address if entity.contact.postal_addresses else ''
                            contact = entity.contact
                            name = '%s %s' % (contact.first_name, contact.last_name)
                            company = contact.company if contact.company else contact.account.name
                            address = '%s\n%s\n%s' % (name, company, address)
                            if inv_addr != address:
                                log.warning('Sale address does not match the entity address IS%s\n%s\n%s', sale.id, inv_addr, address)
                                errors.append([sale.id, inv_addr, address])
                    except Exception, ex:
                        log.error('Error %s, %s, %s', sale.id, entity.id, ex)
                        sys.exit(-1)

    return errors

def verify_entities(sales):
    for sale in sales:
        entity = None
        for charge in sale.charges:
            if not entity:
                entity = charge.parent 
            if entity != charge.parent:
                    raise Exception ('Charge does not have same entity %s', charge.id)
