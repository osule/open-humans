from datetime import datetime

from autoslug import AutoSlugField

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models

from open_humans.models import Member


class BaseStudyUserData(models.Model):
    """
    Abstract base class for study UserData models.

    When implemented, a user field should be defined as AutoOneToOne to
    a User from django.contrib.auth.models.
    """

    class Meta:
        abstract = True

    @property
    def is_connected(self):
        """
        A study is connected if the user has 1 or more access tokens for the
        study's OAuth2 application.
        """
        authorization = (
            self.user.accesstoken_set
            .filter(
                application__user__username='api-administrator',
                application__name=self._meta.app_config.verbose_name)
            .count()) > 0

        return authorization

    @property
    def has_key_data(self):
        """
        Return false if key data needed for data retrieval is not present.
        """
        return self.is_connected

    def get_retrieval_params(self):
        raise NotImplementedError


class Researcher(models.Model):
    """
    Represents an Open Humans researcher.
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    name = models.CharField(max_length=48)

    approved = models.NullBooleanField()


class Study(models.Model):
    """
    Stores information about a study.
    """

    researchers = models.ManyToManyField(Researcher)

    title = models.CharField(max_length=128)
    slug = AutoSlugField(populate_from='title', unique=True)

    description = models.TextField()

    website = models.CharField(max_length=128)

    principal_investigator = models.CharField(max_length=128)
    organization = models.CharField(max_length=128)

    is_live = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)


class DataRequest(models.Model):
    """
    Stores the data requests (a DataFile and a subtype) for a Study.
    """

    # TODO: add the reverse name here so we can refer to `data_requests`
    study = models.ForeignKey(Study)
    # TODO: filter to data file ContentTypes, maybe in pre_save or form?
    data_file_model = models.ForeignKey(ContentType)
    subtype = models.TextField()
    required = models.BooleanField(default=False)

    def __unicode__(self):
        return '{}, {}/{}, {}'.format(
            self.study.title,
            self.app_name(),
            self.subtype,
            'required' if self.required else 'not required')

    @property
    def request_key(self):
        return '{}-{}'.format(self.app_key(), self.subtype)

    def app_key(self):
        return (self.data_file_model.model_class()._meta.app_config.name
                .split('.')[-1])

    def app_name(self):
        return self.data_file_model.model_class()._meta.app_config.verbose_name


class StudyGrant(models.Model):
    """
    Tracks members who have joined a study and approved access to their data.
    """

    study = models.ForeignKey(Study)
    member = models.ForeignKey(Member)

    # XXX: should these all be validated so that they belong to the linked
    # study?
    data_requests = models.ManyToManyField(DataRequest)

    created = models.DateTimeField(auto_now_add=True)
    revoked = models.DateTimeField(null=True)

    def __unicode__(self):
        return '{}, {}, [{}]'.format(
            self.member.user.username,
            self.study.title,
            ', '.join(['{}/{}'.format(r.app_name(), r.subtype)
                       for r in self.data_requests.all()]))

    @property
    def valid(self):
        return (not self.revoked or
                self.revoked >= datetime.now())

    def revoke(self):
        self.revoked = datetime.now()
        self.save()
