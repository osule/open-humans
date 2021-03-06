from django.core.urlresolvers import reverse_lazy

from activities.app_configs import UploadAppConfig


class GenomeExomeConfig(UploadAppConfig):
    """
    Configure the Genome/Exome data application.
    """

    name = __package__
    verbose_name = 'Genome/Exome Data'

    url_slug = 'genome-exome-data'

    href_connect = reverse_lazy('activities:genome-exome-data:manage-files')
    href_add_data = reverse_lazy('activities:genome-exome-data:manage-files')
    retrieval_url = reverse_lazy(
        'activities:genome-exome-data:request-data-retrieval')

    description = """Do you have genome or exome data? You can upload genome,
                     exome, and genotyping data in VCF format."""

    data_description = {
        'name': 'Genetic data (VCF format)',
        'description': (
            'Genome, exome, or genotyping data (VCF format). May reveal '
            "information about health, traits, ancestry, and who you're "
            'related to.'),
    }
