import ckan.plugins.toolkit as toolkit
import ckan.authz as authz
import ckan.logic
import ckan.logic.auth as logic_auth
from ckanext.restricted import logic
from logging import getLogger
log = getLogger(__name__)

@toolkit.auth_allow_anonymous_access
def restricted_resource_show(context, data_dict=None):
    # Ensure user who can edit the package can see the resource
    resource = data_dict.get('resource', context.get('resource',{}))
    if not resource:
       resource = logic_auth.get_resource_object(context, data_dict)
    if type(resource) is not dict:
        resource = resource.as_dict()
    if authz.is_authorized('package_update', context,
                           {'id': resource.get('package_id')}).get('success'):
        return ({'success': True })

    # custom restricted check
    auth_user_obj = context.get('auth_user_obj', None)
    user_name = ""
    if auth_user_obj:
        user_name = auth_user_obj.as_dict().get('name','')
    else:
        if authz.get_user_id_for_username(context.get('user'), allow_none=True):
            user_name = context.get('user','')

    package = data_dict.get('package', {})
    if not package:
        model = context['model']
        package = model.Package.get(resource.get('package_id'))
        package = package.as_dict()
    return logic.restricted_check_user_resource_access(user_name, resource, package)
