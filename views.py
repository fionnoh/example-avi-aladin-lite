"""
GAVIP Example AVIS: Simple AVI

@req: SOW-FUN-010
@req: SOW-FUN-040
@req: SOW-FUN-046
@req: SOW-INT-001
@comp: AVI Web System

This is a simple example AVI which demonstrates usage of the GAVIP AVI framework

Here in views.py, you can define any type of functions to handle
HTTP requests. Any of these functions can be used to create an
AVI query from your AVI interface.
"""
import os
import time
import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.core import serializers
from django.utils import formats
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_http_methods

from avi.models import DemoModel, QueryModel
from pipeline.models import AviJobRequest

from pipeline import manager

from gavip_avi.decorators import require_gavip_role  # use this to restrict access to views in an AVI
ROLES = settings.GAVIP_ROLES

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@require_http_methods(["GET"])
def index(request):
    """
    This view is the first view that the user sees
    We send a dictionary called a context, which contains
    'millis', 'standalone' and 'listdir' variables.
    """
    listdir = os.listdir(settings.INPUT_PATH)
    context = {
        "millis": int(round(time.time() * 1000)),
        "standalone": False,  # This stops the base template rendering the navbar on top
        "show_welcome": request.session.get('show_welcome', True),
        'listdir': listdir
    }
    request.session['show_welcome'] = False
    return render(request, 'avi/index.html', context)


@require_http_methods(["POST"])
def run_query(request):
    """
    This is called when the user submits their job parameters in
    their interface.

    We pull the parameters from the request POST parameters.

    We create an avi_job_request, which must be used to create
    the DemoModel instance, so that the pipeline can excercise
    the pipeline correctly.

    We attach the job_request instance to the DemoModel; this
    extends the AviJob class, which is required for pipeline
    processing.

    We start the job using the job_request ID, and return the
    ID to the user so they can view progress.
    """
    outfile = request.POST.get("outfile")
    adql_query = request.POST.get("query")
    ram_allocation = request.POST.get("ramalloc")

    job = QueryModel.objects.create(
        query=adql_query,
        outputFile=outfile,
        resources_ram_mb=ram_allocation
    )
    return JsonResponse({})


@require_http_methods(["POST"])
def run_votable(request):
    """
    This is called when the user submits their job parameters in
    their interface.

    We pull the parameters from the request POST parameters.

    We create an avi_job_request, which must be used to create
    the DemoModel instance, so that the pipeline can excercise
    the pipeline correctly.

    We attach the job_request instance to the DemoModel; this
    extends the AviJob class, which is required for pipeline
    processing.

    We start the job using the job_request ID, and return the
    ID to the user so they can view progress.
    """
    outfile = request.POST.get("outfile")
    sharedfile = request.POST.get("input_vot")
    ram_allocation = request.POST.get("ramalloc")

    job = DemoModel.objects.create(
        sharedfile=sharedfile,
        outputFile=outfile,
        resources_ram_mb=ram_allocation
    )
    return JsonResponse({})


@require_http_methods(["GET"])
def job_result(request, job_id):
    job = get_object_or_404(AviJobRequest, job_id=job_id)
    file_path = manager.get_pipeline_status(job_id)['output']
    context = {'job_id': job_id}
    with open(file_path, 'r') as out_file:
        context.update(json.load(out_file))
    return render(request, 'avi/job_result.html', context=context)


@require_http_methods(["GET"])
def job_source_result(request, job_id, source_id):
    """
    Load the resource for a job_id, source pair
    """
    job_output_path = manager.get_pipeline_status(job_id)['output']
    context = {}
    context['job_id'] = job_id

    # TODO: the location will need to be refactored. It currently assumes that the json
    # is at ...
    source_details_path = os.path.join(os.path.dirname(job_output_path), '%s_%s_details' % (job_id, source_id))
    with open(source_details_path, 'r') as out_file:
        context.update(json.load(out_file))
    return render(request, 'avi/source_details.html', context=context)


@require_http_methods(["GET"])
def job_result_public(request, job_id, celery_task_id):
    """
    @req: REQ-0035
    @comp: AVI Authentication and Authorization
    """
    job = get_object_or_404(AviJobRequest, job_id=job_id)
    if celery_task_id == job.request.celery_task_id:
        return job_result(request, job_id)
    else:
        raise ObjectDoesNotExist("Invalid public URL")
