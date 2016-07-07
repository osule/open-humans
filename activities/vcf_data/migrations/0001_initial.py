# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-07-07 19:44
from __future__ import unicode_literals

import common.fields
import data_import.utils
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('genome_file', models.FileField(max_length=1024, null=True, upload_to=data_import.utils.get_upload_path)),
                ('user', common.fields.AutoOneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='vcf_data', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Genome and exome data',
                'verbose_name_plural': 'Genome and exome data',
            },
        ),
        migrations.CreateModel(
            name='VCFData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vcf_file', models.FileField(max_length=1024, upload_to=data_import.utils.get_upload_path)),
                ('vcf_source', models.CharField(choices=[(b'', b'--------'), (b'illumina_uyg', b'Illumina Understand Your Genome'), (b'full_genomes_corp', b'Full Genomes Corp'), (b'veritas_genetics', b'Veritas Genetics'), (b'genos_exome', b'Genos'), (b'twenty_three_and_me', b'23andMe Exome Pilot'), (b'dna_land', b'DNALand Genome Imputation'), (b'other', b'Other')], default=b'', max_length=30)),
                ('additional_notes', models.TextField(blank=True, help_text=b'Additional notes (optional)')),
                ('user_data', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vcf_data.UserData')),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
    ]
