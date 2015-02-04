import json
import os
import requests
import urlparse

from collections import OrderedDict
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.dispatch import receiver

from raven.contrib.django.raven_compat.models import client

import account.signals


def get_upload_dir(datafile_model, user):
    """
    Construct the upload dir path for a given User and DataFile model.
    """
    return "member/%s/imported-data/%s/" % (user.username,
                                            datafile_model._meta.app_label)


def get_upload_path(instance, filename=''):
    """
    Construct the upload path for a given DataFile and filename.
    """
    return "%s%s" % (get_upload_dir(type(instance),
                                    instance.user_data.user),
                     filename)


class DataRetrievalTask(models.Model):
    """
    Model for tracking DataFile import requests.

    The datafile_model field stores a ContentType referring to the app-specific
    DataFile model appropriate for files (if any) generated by the task.

    A DataRetrievalTask is related to DataFile models as a ForeignKey.

    Fields:
        status          (IntegerField): Task status, choices defined by
                        self.TASK_STATUS_CHOICES
        request_time    (DateTimeField): Time task was requested by user.
        start_time      (DateTimeField): Time task was sent to processing.
        complete_time   (DateTimeField): Time task reported as complete/failed.
        datafile_model  (ForeignKey): ContentType for DataFile model used for
                        files (if any) created by this task's data import.
        user            (ForeignKey): User that requested this import task.
        app_task_params (TextField): JSON string with app-specific task params,
                        e.g. sample/user IDs. Default is blank.
    """
    TASK_SUCCESSFUL = 0  # Celery task complete, successful.
    TASK_SUBMITTED = 1   # Sent to Open Humans Data Processing.
    TASK_FAILED = 2      # Celery task complete, failed.
    TASK_QUEUED = 3      # OH Data Processing has sent to broker.
    TASK_INITIATED = 4   # Celery has received and started the task.
    TASK_POSTPONED = 5   # Task not submitted yet (eg pending email validation)

    TASK_STATUS_CHOICES = OrderedDict(
        [(TASK_SUCCESSFUL, 'Completed successfully'),
         (TASK_SUBMITTED, 'Submitted'),
         (TASK_FAILED, 'Failed'),
         (TASK_QUEUED, 'Queued'),
         (TASK_INITIATED, 'Initiated'),
         (TASK_POSTPONED, 'Postponed')])

    status = models.IntegerField(choices=TASK_STATUS_CHOICES.items(),
                                 default=TASK_SUBMITTED)
    start_time = models.DateTimeField(default=datetime.now)
    complete_time = models.DateTimeField(null=True)
    datafile_model = models.ForeignKey(ContentType)
    user = models.ForeignKey(User)
    app_task_params = models.TextField(default='')

    def __unicode__(self):
        return '%s:%s:%s' % (self.user,
                             self.source,
                             self.TASK_STATUS_CHOICES[self.status])

    @property
    def source(self):
        return self.datafile_model.model_class()._meta.app_label

    def start_task(self):
        # Target URL is automatically determined from relevant app label.
        task_url = urlparse.urljoin(
            settings.DATA_PROCESSING_URL,
            self.datafile_model.model_class()._meta.app_label)
        try:
            task_req = requests.get(
                task_url,
                params={'task_params': json.dumps(self.get_task_params())})
        except requests.exceptions.RequestException as request_error:
            print "Error in sending request to data processing"
            print self.get_task_params()
            error_message = "Error in call to Open Humans Data Processing."
        if 'task_req' in locals() and not task_req.status_code == 200:
            print "Non-200 response from request sent to data processing"
            print self.get_task_params()
            error_message = "Open Humans Data Processing not returning 200."
        if 'error_message' in locals():
            # Note: could change later if processing works anyway
            self.status = self.TASK_FAILED
            self.save()
            client.captureMessage(error_message,
                                  error_data=self.__base_task_params())

    def postpone_task(self):
        self.status = self.TASK_POSTPONED
        self.save()

    def get_task_params(self):
        params = json.loads(self.app_task_params)
        params.update(self.__base_task_params())
        return params

    def __base_task_params(self):
        """Task parameters all tasks use. Subclasses may not override."""
        uri_scheme = 'https://'
        if settings.DEBUG == True:
            uri_scheme = 'http://'
        s3_key_dir = get_upload_dir(self.datafile_model.model_class(),
                                    self.user)
        s3_bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        update_url = urlparse.urljoin(uri_scheme + settings.DOMAIN,
                                      '/data-import/task-update/')
        return {'s3_key_dir': s3_key_dir,
                's3_bucket_name': s3_bucket_name,
                'task_id': self.id,
                'update_url': update_url}


@receiver(account.signals.email_confirmed)
def start_postponed_tasks(email_address, **kwargs):
    postponed_tasks = DataRetrievalTask.objects.filter(
        status=DataRetrievalTask.TASK_POSTPONED,
        user=email_address.user)
    for task in postponed_tasks:
        task.start_task()


class BaseDataFile(models.Model):
    """
    Attributes that need to be defined in subclass:
        task:      ForeignKey to data_import.DataRetrievalTask with an
                   app-specific related_name argument.
        user_data: ForeignKey to an app-specific model (i.e. UserData) which
                   has a 'user' field that is a OneToOenField to User.
    """
    file = models.FileField(upload_to=get_upload_path)
    task = None
    user_data = None

    class Meta:
        abstract = True

    def __unicode__(self):
        return '%s:%s:%s' % (self.user_data.user,
                             self.source,
                             self.file)

    @property
    def source(self):
        return self._meta.app_label

    @property
    def basename(self):
        return os.path.basename(self.file.name)
