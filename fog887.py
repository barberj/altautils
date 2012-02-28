# fog887.py
"""
Candidates were added as clients to Strategic Legal. This allowed them to
add tests.

Clean all clients from strategic legal that don't have strategic legal domain email address.
"""

import erp.model as m

def update():
    strategic = m.Account.get(21674)
    print 'Found %s contacts' % len(strategic.contacts)
    count = 0
    for contact in strategic.contacts:
        # check for internal
        if not 'strategiclegal' in contact.user.username:
            found_cp = False
            if contact.candidate and contact.candidate.candidate_profiles:
                for profile in contact.candidate.candidate_profiles:
                    if profile.account.parent_account == strategic:
                        found_cp = True
                        count += 1
                if not found_cp:
                    print 'No strategic profile for %s %s' % (contact.full_name, contact.id)
                else:
                    pass
                    #print 'Fixing %s %s' % (contact.full_name, contact.id)
                    #m.meta.Session.delete(contact.client)
                    #contact.company=''
                    #m.meta.Session.commit()
                    #contact.account = None
                    #m.meta.Session.commit()
            else:
                print 'No candidate profile for %s %s %s' % (contact.full_name, contact.id, contact.user.username)
                try:
                    m.meta.Session.delete(contact)
                except Exception, ex:
                    print 'Unable to delete %s %s %s' % (contact.full_name, contact.id, contact.user.username)
                    m.meta.Session.rollback()
        m.meta.Session.commit()

    print 'Found %s contacts with profile' % count


def update_single(username):
    user = m.User.get_by(username=username)
    contact = user.contact
    if contact:
        print 'Fixing contact %s' % contact.full_name
        contact.company = ''

        if contact.account:
            contact.account = None

        if contact.client:
            m.meta.Session.delete(contact.client)

        m.meta.Session.commit()
