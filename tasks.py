"""
GAVIP Example AVIS: Data Sharing AVI

An example AVI pipeline is defined here, consisting of one task:

- ProcessData - generates HTML from a VOTable
"""

import os
import time
import json
import logging
from django.conf import settings

import matplotlib
# Run without UI
matplotlib.use('Agg')
import numpy as np
from astropy.table import Table
import pandas_profiling
import pandas as pd

# Class used for creating pipeline tasks
from pipeline.classes import (
    AviTask,
    AviParameter, AviLocalTarget,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# Service enabling ADQL queries to be run in GACS(-dev)
# Queries are run asynchronously, but the service is restricted to anonymous users until ESAC CAS integration is possible.
import services.gacs as svc_gacs


class ProcessData(AviTask):
    """
    This function requires a VOTable as an input.
    """
    sharedfile = AviParameter()
    outputFile = AviParameter()

    def output(self):
        return AviLocalTarget(os.path.join(
            settings.OUTPUT_PATH, self.outputFile
        ))

    def run(self):

        """
        Analyses the VOTable file containing the GACS-dev query results
        """
        shared_file_path = os.path.join(
            settings.INPUT_PATH, self.sharedfile
        )
        logger.debug('Input VOTable file: %s' % shared_file_path)
        t = Table.read(shared_file_path, format='votable')
        df = pd.DataFrame(np.ma.filled(t.as_array()), columns=t.colnames)
        gaiamagcols = ['source_id', 'mag_bj', 'mag_g', 'mag_grvs', 'mag_rf', 'ra', 'dec']
        gaiadf = df[gaiamagcols]

        sources = []

        # for i in range(0, 5):
        for i in range(0, len(gaiadf.index)):
            temp_json = json.loads(df.iloc[i].to_json())
            temp_json['id'] = i
            # temp_json['request_id'] = self.request_id
            sources.append(temp_json)

        analysis_context = {'sources': sources}

        for source in sources:
            temp_id = source['id']
            source_details = {}
            for i in df:
                source_details[i] = source[i]
            with open(os.path.join(settings.OUTPUT_PATH, '%s_%s_details' % (self.request_id, temp_id)), 'wb') as out:
                json.dump(source_details, out)

        # JSON will be the context used for the template
        with open(self.output().path, 'wb') as out:
            json.dump(analysis_context, out)


class DownloadData(svc_gacs.GacsQuery):
    """
    This task uses an AVI service, to obtain a data product from GACS.
    Notice that we do not define a 'run' function! It is defined by the
    service class which we extend.

    See :class:`GacsQuery`
    """
    query = AviParameter()
    outputFile = AviParameter()

    def output(self):
        return AviLocalTarget(os.path.join(
            settings.OUTPUT_PATH, 'simulatedData_%s.vot' % self.outputFile
        ))


class QueryData(AviTask):
    """
    This function requires a DownloadData class to be run.
    We will obtain GACS data in this way.

    Once we have this data, we parse the VOTable.
    """
    query = AviParameter()
    outputFile = AviParameter()

    def output(self):
        return AviLocalTarget(os.path.join(
            settings.OUTPUT_PATH, self.outputFile
        ))

    def requires(self):
        return self.task_dependency(DownloadData)

    def run(self):

        """
        Analyses the VOTable file containing the GACS-dev query results
        """
        logger.info('Input VOTable file: %s' % self.input().path)
        t = Table.read(self.input().path, format='votable')
        df = pd.DataFrame(np.ma.filled(t.as_array()), columns=t.colnames)

        gaiamagcols = ['source_id', 'mag_bj', 'mag_g', 'mag_grvs', 'mag_rf', 'ra', 'dec']
        gaiadf = df[gaiamagcols]

        sources = []

        # for i in range(0, 5):
        for i in range(0, len(gaiadf.index)):
            temp_json = json.loads(df.iloc[i].to_json())
            temp_json['id'] = i
            # temp_json['request_id'] = self.request_id
            sources.append(temp_json)

        analysis_context = {'sources': sources}

        for source in sources:
            temp_id = source['id']
            source_details = {}
            for i in df:
                source_details[i] = source[i]
            with open(os.path.join(settings.OUTPUT_PATH, '%s_%s_details' % (self.request_id, temp_id)), 'wb') as out:
                json.dump(source_details, out)

        # JSON will be the context used for the template
        with open(self.output().path, 'wb') as out:
            json.dump(analysis_context, out)