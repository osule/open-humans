# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-08 04:56
from __future__ import unicode_literals

import datetime

from string import digits  # pylint: disable=deprecated-module

from django.db import migrations

from common.utils import generate_id


def migrate_keeping_pace(apps, schema_editor):
    Application = apps.get_model('oauth2_provider', 'Application')
    Study = apps.get_model('studies', 'Study')
    StudyGrant = apps.get_model('studies', 'StudyGrant')
    Member = apps.get_model('open_humans', 'Member')
    OAuth2DataRequestProject = apps.get_model('private_sharing',
                                              'OAuth2DataRequestProject')
    DataRequestProjectMember = apps.get_model('private_sharing',
                                              'DataRequestProjectMember')

    try:
        rumi = Member.objects.get(user__username='rumichunara')
    except Member.DoesNotExist:
        return

    def random_project_member_id():
        code = generate_id(size=8, chars=digits)

        while DataRequestProjectMember.objects.filter(
                project_member_id=code).count() > 0:
            code = generate_id(size=8, chars=digits)

        return code

    project = OAuth2DataRequestProject()

    project.is_study = True
    project.name = 'Keeping Pace'
    project.slug = 'keeping-pace'
    project.leader = 'Dr. Rumi Chunara'
    project.organization = 'New York University'
    project.is_academic_or_nonprofit = True
    project.contact_email = 'keepingpace@chunaralab.com'
    project.info_url = 'https://keeping-pace.chunaralab.com/'
    project.short_description = ('Dynamic Assessment of Environment and '
                                 'Exercise Using Personal Health Data')
    project.long_description = ('Dynamic Assessment of Environment and '
                                'Exercise Using Personal Health Data')
    project.active = True
    project.badge_image = 'private-sharing/badges/migrated/keeping-pace.png'
    project.request_sources_access = ['runkeeper']
    project.request_message_permission = False
    project.request_username_access = False
    project.coordinator = rumi
    project.approved = True
    project.created = datetime.datetime(2015, 6, 23, 6, 15, 1, 544000)

    project.enrollment_url = 'https://keeping-pace.chunaralab.com/'
    project.redirect_url = ('https://keeping-pace.chunaralab.com'
                            '/accounts/openhumans/login/callback/')

    project.application = Application.objects.get(name='Keeping Pace')

    project.save()

    # Migrate each StudyGrant to a DataRequestProjectMember
    for grant in StudyGrant.objects.all():
        if grant.revoked:
            continue

        project_member = DataRequestProjectMember()

        project_member.project = project
        project_member.member_id = grant.member_id
        project_member.project_member_id = random_project_member_id()
        project_member.sources_shared = ['runkeeper']
        project_member.joined = True
        project_member.authorized = True

        project_member.save()

    # Delete original Study
    Study.objects.all().delete()

    # Delete original StudyGrants
    StudyGrant.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('open_humans', '0016_auto_20150410_2301'),
        ('private_sharing', '0026_auto_20160328_1943'),
        ('studies', '0019_auto_20160311_0137'),
    ]

    operations = [
        migrations.RunPython(migrate_keeping_pace),
    ]