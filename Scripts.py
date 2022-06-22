"""
Model exported as python.
Name : Modelv2
Group : 
With QGIS : 32207
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterVectorDestination
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class Modelv2(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('dem', 'DEM', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorDestination('Cuenca', 'Cuenca', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Centroides', 'Centroides', type=QgsProcessing.TypeVectorPoint, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('RedHidrica', 'Red Hidrica', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Cuencas', 'Cuencas', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(9, model_feedback)
        results = {}
        outputs = {}

        # Fill Sinks (Wang & Liu)
        alg_params = {
            'ELEV': parameters['dem'],
            'MINSLOPE': 0.1,
            'FDIR': QgsProcessing.TEMPORARY_OUTPUT,
            'FILLED': QgsProcessing.TEMPORARY_OUTPUT,
            'WSHED': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FillSinksWangLiu'] = processing.run('saga:fillsinkswangliu', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Analisis Cuenca 
        alg_params = {
            '-4': False,
            '-a': False,
            '-b': False,
            '-m': False,
            '-s': False,
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'blocking': None,
            'convergence': 5,
            'depression': None,
            'disturbed_land': None,
            'elevation': outputs['FillSinksWangLiu']['FILLED'],
            'flow': None,
            'max_slope_length': 0,
            'memory': 300,
            'threshold': 10000,
            'basin': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AnalisisCuenca'] = processing.run('grass7:r.watershed', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # r.to.vect
        alg_params = {
            '-b': False,
            '-s': True,
            '-t': False,
            '-v': False,
            '-z': False,
            'GRASS_OUTPUT_TYPE_PARAMETER': 0,  # auto
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'GRASS_VECTOR_DSCO': '',
            'GRASS_VECTOR_EXPORT_NOCAT': False,
            'GRASS_VECTOR_LCO': '',
            'column': 'value',
            'input': outputs['AnalisisCuenca']['basin'],
            'type': 2,  # area
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Rtovect'] = processing.run('grass7:r.to.vect', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Channel Network and Drainage Basins
        alg_params = {
            'DEM': outputs['FillSinksWangLiu']['FILLED'],
            'THRESHOLD': 5,
            'BASIN': QgsProcessing.TEMPORARY_OUTPUT,
            'BASINS': QgsProcessing.TEMPORARY_OUTPUT,
            'CONNECTION': QgsProcessing.TEMPORARY_OUTPUT,
            'DIRECTION': QgsProcessing.TEMPORARY_OUTPUT,
            'NODES': QgsProcessing.TEMPORARY_OUTPUT,
            'ORDER': QgsProcessing.TEMPORARY_OUTPUT,
            'SEGMENTS': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ChannelNetworkAndDrainageBasins'] = processing.run('saga:channelnetworkanddrainagebasins', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Delimitar Cuenca
        alg_params = {
            '-4': False,
            '-a': False,
            '-b': False,
            '-m': True,
            '-s': True,
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'blocking': None,
            'convergence': 5,
            'depression': None,
            'disturbed_land': None,
            'elevation': outputs['FillSinksWangLiu']['FILLED'],
            'flow': None,
            'max_slope_length': 0,
            'memory': 300,
            'threshold': 20000,
            'basin': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DelimitarCuenca'] = processing.run('grass7:r.watershed', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Convertir a Vector
        alg_params = {
            '-b': False,
            '-s': True,
            '-t': False,
            '-v': False,
            '-z': False,
            'GRASS_OUTPUT_TYPE_PARAMETER': 0,  # auto
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'GRASS_VECTOR_DSCO': '',
            'GRASS_VECTOR_EXPORT_NOCAT': False,
            'GRASS_VECTOR_LCO': '',
            'column': 'value',
            'input': outputs['DelimitarCuenca']['basin'],
            'type': 2,  # area
            'output': parameters['Cuenca']
        }
        outputs['ConvertirAVector'] = processing.run('grass7:r.to.vect', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Cuenca'] = outputs['ConvertirAVector']['output']

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Cortar Cuencas 
        alg_params = {
            'INPUT': outputs['Rtovect']['output'],
            'OVERLAY': outputs['ConvertirAVector']['output'],
            'OUTPUT': parameters['Cuencas']
        }
        outputs['CortarCuencas'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Cuencas'] = outputs['CortarCuencas']['OUTPUT']

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Red Hidríca
        alg_params = {
            'INPUT': outputs['ChannelNetworkAndDrainageBasins']['SEGMENTS'],
            'OVERLAY': outputs['ConvertirAVector']['output'],
            'OUTPUT': parameters['RedHidrica']
        }
        outputs['RedHidrca'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['RedHidrica'] = outputs['RedHidrca']['OUTPUT']

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Centroides
        alg_params = {
            'ALL_PARTS': False,
            'INPUT': outputs['CortarCuencas']['OUTPUT'],
            'OUTPUT': parameters['Centroides']
        }
        outputs['Centroides'] = processing.run('native:centroids', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Centroides'] = outputs['Centroides']['OUTPUT']
        return results

    def name(self):
        return 'Modelv2'

    def displayName(self):
        return 'Modelv2'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Modelv2()
