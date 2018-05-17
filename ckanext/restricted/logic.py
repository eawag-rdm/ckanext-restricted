import ckan.lib.mailer as mailer
from email.header import Header
import ckan.logic as logic
from ckan.lib.base import render_jinja2
import ckan.plugins.toolkit as toolkit
from json import loads

try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config

from logging import getLogger
log = getLogger(__name__)

def restricted_check_user_resource_access(user, resource_dict, package_dict):
    ''' Checks whether user can access resource. Considers 3 levels:
          + public
          + same_organization
          + only_allowed_users
    The latter two are additive: You can give permision to your orga and then
    some more.

    '''

    restricted_level = resource_dict.get('restricted_level', 'public')
    try:
        # are the allowwed_users in a json-list?
        allowed_users = loads(resource_dict.get('allowed_users', '[]'))
        if not isinstance(allowed_users, list):
            raise
    except:
        # then they better be a comma separated string.
        allowed_users = resource_dict.get('allowed_users', '').split(',')

    # Public resources (DEFAULT)
    if restricted_level == 'public':
        return {'success': True }
    
    # Anonymous can't have access to restricted resources
    if not user:
        return {'success': False,
                'msg': 'No access for anonymous users'}
        
    if user in allowed_users:
        # User explicitly allowed
        return {'success': True}

    if restricted_level == 'only_allowed_users':
        return {'success': False,
                'msg': 'Access restricted to allowed users only'}
    elif restricted_level == 'same_organization':
        orga_id = package_dict.get('owner_org')
        data_dict = {'permission': 'read', 'id': user}
        user_orgs = toolkit.get_action(
            'organization_list_for_user')(None, data_dict)
        user_orgs = [x.get('id') for x in user_orgs if x.get('id')]

        if orga_id in user_orgs:
            return {'success': True}
        else:
            return {'success': False,
                    'msg': ('Access restricted to same organization'
                                ' ({}) members'.format(orga_id))}
    else:
        msg = 'Unknown restriction level: "{}" for resource {}'.format(
            restricted_level, resource_dict.get('id'))
        log.error(msg)
        return {'success': False, 'msg': msg}


def restricted_mail_allowed_user(user_id, resource):
 
    # Get user information
    context = {}
    context['ignore_auth'] = True
    context['keep_email'] = True
    user = toolkit.get_action('user_show')(context, {'id': user_id})
    user_email = user['email']
    user_name = Header(
        u'"{}"'.format(user.get('display_name', user['name'])),
        'utf-8').encode('utf-8')

    resource_name = resource.get('name', resource['id'])
    mail_body = restricted_allowed_user_mail_body(user, resource)
    mail_subject = ('Access granted to resource {}'
                    .format(resource_name).encode('utf-8'))
    admin_email = config.get('email_to')
    try:
        # Send mail to user
        mailer.mail_recipient(user_name, user_email, mail_subject,
                              mail_body, headers={'Reply-To': admin_email})
    except:
        log.error('Failed to send mail to "{}"'.format(user_email))
    try:
        # Send a copy to admin
        mailer.mail_recipient('CKAN Admin', admin_email,
                              'Fwd: {}'.format(mail_subject), mail_body)
    except:
        log.error('Failed to send mail to "{}"'.format(admin_email))

        
def restricted_allowed_user_mail_body(user, resource):
    resource_link = toolkit.url_for(
        controller='package', action='resource_read',
        id=resource.get('package_id'), resource_id=resource.get('id'))

    extra_vars = {
        'site_title': config.get('ckan.site_title'),
        'site_url': config.get('ckan.site_url'),
        'user_name': user.get('display_name', user['name']),
        'resource_name': resource.get('name', resource['id']),
        'package_name': resource.get('package_name','No FUCKING PACKAGE_NAME'),
        'package_id': resource.get('package_id','No FUCKING PACKAGE_ID'),
        'resource_link': config.get('ckan.site_url') + resource_link,
        'resource_url': resource.get('url')
        }

    return render_jinja2('restricted/emails/restricted_user_allowed.txt', extra_vars)

def restricted_notify_allowed_users(previous_value, updated_resource):
    previous_allowed_users = set(previous_value.split(','))
    updated_allowed_users =  set(updated_resource.get('allowed_users', '')
                                 .split(','))
    notify_users = updated_allowed_users - previous_allowed_users
    for user_id in notify_users:
        restricted_mail_allowed_user(user_id, updated_resource)



