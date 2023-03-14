from importlib import reload
from typing import List

import arcpy

import usgs_gages


class Toolbox(object):
    def __init__(self):
        self.label =  "Gages toolbox"
        self.alias  = "gages"

        # List of tool classes associated with this toolbox
        self.tools = [GetUsgsGages] 


class GetUsgsGages(object):
    def __init__(self):
        self.label       = "Get USGS Gages"
        self.description = "Download USGS gage locations from the USGS waterdata API."

    def getParameterInfo(self):
        extent = arcpy.Parameter(
            displayName="Gage query extent",
            name="extent",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        extent.filter.list = ["Polygon"]
        
        out_features = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Output")

        site_status = arcpy.Parameter(
            displayName="Site status",
            name="site_status",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        site_status.value = usgs_gages.UsgsSiteStatus.ALL.value
        site_status.filter.list = [s.value for s in usgs_gages.UsgsSiteStatus]

        clip = arcpy.Parameter(
            displayName="Clip to extent features",
            name="clip",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        clip.value = False

        overwrite = arcpy.Parameter(
            displayName="Overwrite output",
            name="overwrite",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        overwrite.value = False
        
        parameters = [extent, out_features, site_status, clip, overwrite]
        
        return parameters

    def isLicensed(self): #optional
        return True

    def updateParameters(self, parameters): #optional
        # if parameters[0].altered:
        #     parameters[1].value = arcpy.ValidateFieldName(parameters[1].value,
        #                                                   parameters[0].value)
        return

    def updateMessages(self, parameters): #optional
        return

    def execute(self, parameters: List[arcpy.Parameter], messages):
        reload(usgs_gages)
        extent = parameters[0].valueAsText
        out_features = parameters[1].valueAsText
        site_status = parameters[2].valueAsText
        clip = parameters[3].value
        overwrite = parameters[4].value
        arcpy.AddMessage(f'{extent}, {parameters[0].value}, {type(parameters[0].value)}')
        arcpy.AddMessage(f'{out_features}, {parameters[1].value}, {type(parameters[1].value)}')
        arcpy.AddMessage(f'{site_status}, {parameters[2].value}, {type(parameters[2].value)}')
        arcpy.AddMessage(f'{clip}, {parameters[3].value}, {type(parameters[3].value)}')
        arcpy.AddMessage(f'{overwrite}, {parameters[4].value}, {type(parameters[4].value)}')
        usgs_gages.get_usgs_gages(extent, out_features, overwrite, clip, usgs_gages.UsgsSiteStatus(site_status))
