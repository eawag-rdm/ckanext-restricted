import re
import ckan.model as model
import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.mailer as mailer

import ckan.plugins.toolkit as toolkit
from ckan.common import _, request, c, g
from ckan.lib.base import render_jinja2
from logging import getLogger
try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config
from email.header import Header
import simplejson as json
import ckan.lib.navl.dictization_functions as dictization_functions
DataError = dictization_functions.DataError
unflatten = dictization_functions.unflatten

render = base.render
log = getLogger(__name__)

class RestrictedController(toolkit.BaseController):

    def __before__(self, action, **env):
        base.BaseController.__before__(self, action, **env)
        try:
            context = {'model': base.model, 'user': base.c.user or base.c.author,
                       'auth_user_obj': base.c.userobj}
            logic.check_access('site_read', context)
        except logic.NotAuthorized:
            base.abort(401, _('Not authorized to see this page'))

    def _send_request_mail(self, data, resource_id):
        access_mail_template = 'restricted/emails/restricted_access_request.txt'
        access_mail_template_cc = 'restricted/emails/restricted_access_request_cc.txt'
        
        resource_link = toolkit.url_for(
            controller='package',
            action='resource_read',
            id=data.get('package_name'),
            resource_id=resource_id)
        
        resource_edit_link = toolkit.url_for(
            controller='package',
            action='resource_edit',
            id=data.get('package_name'),
            resource_id=resource_id)

        organame = data.get('pkg_dict').get('organization').get('name')
        datamanager = toolkit.get_action('eaw_schema_datamanger_show')(
            data_dict={'organization': organame})
            
        extra_vars = {
            'site_title': config.get('ckan.site_title'),
            'site_url': config.get('ckan.site_url'),
            'maintainer_name': data.get('maintainer_name'),
            'maintainer_email': data.get('maintainer_name'),
            'user_id': data.get('user_id'),
            'user_name': data.get('user_name'),
            'user_email': data.get('user_email'),
            'resource_name': data.get('resource_name'),
            'resource_link': config.get('ckan.site_url') + resource_link,
            'resource_edit_link': (config.get('ckan.site_url')
                                   + resource_edit_link),
            'package_name': data.get('package_name'),
            'message': data.get('message'),
            'admin_email_to': config.get('email_to'),
            'data_manager_name': datamanager.get('fullname'),
            'data_manager_homepage': datamanager.get('homepage')
        }

        body = render_jinja2(access_mail_template, extra_vars)
        subject = Header(
            'Access request for  ' + data.get('package_name')
            + '/' + data.get('resource_name'), 'utf-8').encode('utf-8')
        recip_name = Header(
            u'"{}"'.format(data.get('maintainer_name')),
            'utf-8').encode('utf-8')
        recip_email = data.get('maintainer_email').encode('utf-8')
        admin_name = ('{} Admin'
                      .format(config.get('ckan.site_title'))
                      .encode('utf-8'))
        admin_email = config.get('email_to').encode('utf-8')
        headers = {'Reply-To': data.get('user_email').encode('utf-8')}
        try:
            mailer.mail_recipient(recip_name, recip_email, subject,
                                  body, headers)
        except mailer.MailerException as mailer_exception:
            error_summary = ('Mail to Usage Contact: {}'
                             .format(mailer_exception))
            log.error(error_summary)
            return error_summary
            
        # A copy goes to the admin. CC doesn't work because ckan.lib.mailer
        # does not parameterize envelope addresss.
        body = render_jinja2(access_mail_template_cc, extra_vars)
        try:
            mailer.mail_recipient(admin_name, admin_email,
                                  subject + ' (copy)', body, headers)
        except mailer.MailerException as mailer_exception:
            error_summary = ('Copy to admin: {}'.format(mailer_exception))
            log.error(error_summary)
            return error_summary
            
        # Copy for requestor
        # Modified message body that does not disclose the links to the resource
        extra_vars['resource_link'] = '[undisclosed]'
        extra_vars['resource_edit_link'] = '[undisclosed]'
        body = render_jinja2(access_mail_template, extra_vars)
        body_user = (u'Please find below a copy of the access request'
                     ' mail sent on your behalf:\n\n-----------------------'
                     '----------------------------------------------------\n'
                     '{}'.format(body) + '\n-------------------------------'
                     '--------------------------------------------\n')
        headers = {'Reply-To': config.get('email_to').encode('utf-8')}
        recip_name = Header(
            u'"{}"'.format(data.get('user_name')), 'utf-8').encode('utf-8')
        try:
            mailer.mail_recipient(recip_name,
                                  data.get('user_email').encode('utf-8'),
                                  'Fwd: ' + subject, body_user, headers)
        except mailer.MailerException as mailer_exception:
            error_summary = 'Copy for requestor: {}'.format(mailer_exception)
            log.error(error_summary)
            return error_summary

        return False

        
    def _send_request(self, resource_id, context=None):
        try:
            data_dict = logic.clean_dict(unflatten(
                logic.tuplize_dict(logic.parse_params(request.params))))
        except logic.NotAuthorized:
            toolkit.abort(401, _('Not authorized to see this page'))
        try:
            data_dict['pkg_dict'] = toolkit.get_action('package_show')(
                context,
                {'id': data_dict.get('package_name')})
        except toolkit.ObjectNotFound:
            toolkit.abort(404, _('Package not found'))
        except:
            toolkit.abort(404, _('Exception retrieving package'))

        # Validation
        errors = {}
        error_summary = {}
        
        if data_dict.get('message', '') == '':
            errors['message'] = [u'Missing Value']
            error_summary['message'] =  u'Missing Value'

        if len(errors) > 0:
            return self.restricted_request_access_form(
                package_id=data_dict.get('package-name'),
                resource_id=data_dict.get('resource'),
                errors=errors, error_summary=error_summary, data=data_dict)

        error_summary = self._send_request_mail(data_dict, resource_id)
        return render('restricted/restricted_request_access_result.html',
                      extra_vars={
                          'data': data_dict,
                          'error_summary': error_summary,
                          'pkg_dict': data_dict.get('pkg_dict')})

    def restricted_request_access_form(self, package_id, resource_id, data={},
                                       errors={}, error_summary={}):
        user_id = toolkit.c.user

        if not user_id:
            toolkit.abort(401, _('Access request form is available to'
                                 ' logged in users only.'))

        if ('save' in request.params) and data and (not errors):
            return self._send_request(resource_id)
        
        if not data:
            user = toolkit.get_action('user_show')(None, {'id': user_id})
            try:
                data['pkg_dict'] = toolkit.get_action(
                    'package_show')(None, {'id': package_id})
            except toolkit.ObjectNotFound:
                toolkit.abort(404, _('Dataset not found'))
            except Exception as e:
                log.warn('Exception Request Form: ' + repr(e))
                toolkit.abort(404, _('Exception retrieving dataset ('
                                     + str(e) + ')'))
            
            data['package_id'] = package_id
            data['resource_id'] = resource_id
            data['user_id'] = user_id
            data['user_name'] = user.get('display_name', user_id)
            data['user_email'] = user.get('email', '')
            data['package_name'] = data['pkg_dict'].get('name')
            data['resource_name'] = ''
            
            for resource in data['pkg_dict'].get('resources', []):
                if resource['id'] == resource_id:
                    data['resource_name'] = resource['name']
                    break
            else:
                toolkit.abort(404, 'Dataset resource not found')

            contact_details = self._get_contact_details(data['pkg_dict'])
            data['maintainer_email'] = contact_details.get('contact_email', '')
            data['maintainer_name'] = contact_details.get('contact_name', '')
            
        else:
            pass
        
        extra_vars = {'pkg_dict': data['pkg_dict'], 'data': data,
                      'errors':errors, 'error_summary': error_summary}
        return render('restricted/restricted_request_access_form.html',
                      extra_vars=extra_vars)

    def _get_contact_details(self, pkg_dict):
        contact_email = ""
        contact_name = ""
        # Usage contact in Lastname, Firstname(s) <name@email.provider.tld> form.
        
        # This defined a valid emai address, according to
        # https://stackoverflow.com/a/201378
        emailregex = (
            '(?:[a-z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\\.[a-z0-9!#$%&\'*+/=?^_`{|}~-]+'
            ')*|\\"(?:[\\x01-\\x08\\x0b\\x0c\\x0e-\\x1f\\x21\\x23-\\x5b\\x5d-\\x'
            '7f]|\\\\[\\x01-\\x09\\x0b\\x0c\\x0e-\\x7f])*\\")@(?:(?:[a-z0-9](?:['
            'a-z0-9-]*[a-z0-9])?\\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\\[(?:(?:(2'
            '(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\\.){3}(?:(2(5[0-5]|[0'
            '-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\\x01-\\x'
            '08\\x0b\\x0c\\x0e-\\x1f\\x21-\\x5a\\x53-\\x7f]|\\\\[\\x01-\\x09\\x0'
            'b\\x0c\\x0e-\\x7f])+)\\])')
        personregex = re.compile('(?P<contact_name>.*?)<(?P<contact_email>'
                                 + emailregex+r')>')
        parsed = re.search(personregex, pkg_dict.get('usage_contact'))
        contact_email = parsed.groupdict().get('contact_email', '')
        contact_name = parsed.groupdict().get('contact_name', '')

        return {'contact_email':contact_email, 'contact_name':contact_name}
