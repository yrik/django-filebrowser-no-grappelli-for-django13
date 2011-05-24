# coding: utf-8

# general imports
import os

# django imports
from django.shortcuts import render_to_response
from django.template import RequestContext as Context
from django.http import HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.dispatch import Signal

# filebrowser imports
from filebrowser.settings import *
from filebrowser.templatetags.fb_tags import query_helper
from filebrowser.functions import get_path, get_settings_var, convert_filename, handle_file_upload

# upload signals
filebrowser_pre_upload = Signal(providing_args=["path", "file"])
filebrowser_post_upload = Signal(providing_args=["path", "file"])

def file_process(request):
    query = request.GET
    path = get_path(query.get('dir', ''))

    abs_path = os.path.join(MEDIA_ROOT, DIRECTORY, path)

    from filebrowser.forms import UploadForm
    form = UploadForm(data=request.POST, files=request.FILES, path=abs_path)

    if form.is_valid():
        f = form.cleaned_data['file']

        f.name = convert_filename(f.name)
        # PRE UPLOAD SIGNAL
        filebrowser_pre_upload.send(sender=request, path=abs_path, file=f)
        # HANDLE UPLOAD
        uploadedfile = handle_file_upload(abs_path, f)
        # POST UPLOAD SIGNAL
        filebrowser_post_upload.send(sender=request, path=abs_path, file=uploadedfile)
    else:
        return form.errors


def upload(request):
    """
    Multiple File Upload.
    """

    # QUERY / PATH CHECK
    query = request.GET
    path = get_path(query.get('dir', ''))
    if path is None:
        msg = _('The requested Folder does not exist.')
        request.user.message_set.create(message=msg)
        return HttpResponseRedirect(reverse("fb_browse"))

    redirect_url = reverse("fb_browse") + query_helper(query, "ot=desc,o=date", "ot,o")

    return render_to_response('filebrowser/upload_uploadify.html', {
        'redirect_url': redirect_url,
        'query': query,
        'settings_var': get_settings_var(),
        'breadcrumbs_title': _(u'Upload'),
        'title': _(u'Select files to upload'),
    }, context_instance=Context(request))

upload = staff_member_required(never_cache(upload))

# Uploadify handler
from uploadify.views import upload_received
def uploadify_received_handler(sender, request, data, **kwargs):
    if (sender=='filebrowser'):
        return file_process(request)
upload_received.connect(uploadify_received_handler)

