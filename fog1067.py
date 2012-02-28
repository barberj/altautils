import logging
logging.root.level = logging.INFO
log = logging

import sys
import datetime

import erp.model as m
import erp.lib.testing_billing as billing

def delete_sale(sale_id):
    sale = m.Sale.get(sale_id)
    if not sale:
        log.error('Unable to get sale')
        return False
    for charge in sale.charges:
        charge.sale = None
    m.meta.Session.delete(sale)
    return True

def move_charges_to_offices(sale_id):

    # get the sale
    sale = m.Sale.get(sale_id)
    if not sale:
        log.error('Unable to get sale')
        return False

    # get the office and charges
    offices = sale.account.testing_account.offices
    charges = sale.charges[:]

    log.info('Moving %s', len(charges))
    # move the charges to the office
    for charge in charges:
        log.info('Trying to move %s', charge.description)
        for office in offices:
            if office.name in charge.description:
                log.info('Found Office %s', office.name)
                charge.account = None
                charge.office = office
                charge.sale = None
    

    # delete/commit
    #m.meta.Session.delete(sale)
    #m.meta.Session.commit()
        
    return charges

def fog1067():
    """
    Thought is delete the sale, set the billing date back and rerun.
    """
    northrop = m.Account.get(11492)

    if northrop:
        essex = [office for office in northrop.testing_account.offices if office.name.lower() == 'essex'][0]
        fairfax = [office for office in northrop.testing_account.offices if office.name.lower() == 'fairfax'][0]
    else:
        log.error('Unable to get account')
        sys.exit(-1)

    if not essex or not fairfax:
        log.error('Unable to get the offices')
        sys.exit(-1)

    # ensure the offices are billable
    if not essex.is_invoiced:
        log.warning('Essex is not billable')
        essex.is_invoiced = True

    if not fairfax.is_invoiced:
        log.warning('Fairfax is not billable')
        fairfax.is_invoiced = True

    # move the charges
    move_charges_to_offices(140603)

    # run billing

    return billing.run_monthly_billing(billing_date=datetime.date(2011,9,30))
