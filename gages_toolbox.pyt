from datetime import datetime
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

        start_dt = arcpy.Parameter(
            displayName="Start date",
            name="start_dt",
            datatype="GPDate",
            parameterType="Optional",
            direction="Input")
        start_dt.value = None

        end_dt = arcpy.Parameter(
            displayName="End date",
            name="end_dt",
            datatype="GPDate",
            parameterType="Optional",
            direction="Input")
        end_dt.value = None

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
        
        parameters = [
            extent,
            out_features,
            site_status,
            start_dt,
            end_dt,
            clip,
            overwrite,
        ]
        
        return parameters

    def isLicensed(self): #optional
        return True

    def updateParameters(self, parameters): #optional
        # if parameters[0].altered:
        #     parameters[1].value = arcpy.ValidateFieldName(parameters[1].value,
        #                                                   parameters[0].value)
        return

    def updateMessages(self, parameters): #optional
        start_dt: datetime = parameters[3].value
        end_dt: datetime = parameters[4].value
        if start_dt and end_dt and start_dt > end_dt:
            parameters[4].setErrorMessage('End date must be after start date')
        return

    def execute(self, parameters: List[arcpy.Parameter], messages):
        reload(usgs_gages)
        extent = parameters[0].valueAsText
        out_features = parameters[1].valueAsText
        site_status = parameters[2].valueAsText
        start_dt: datetime = parameters[3].value
        end_dt: datetime = parameters[4].value
        clip: bool = parameters[5].value
        overwrite: bool = parameters[6].value
        arcpy.AddMessage(f'Extent: {extent}')
        arcpy.AddMessage(f'Output features: {out_features}')
        arcpy.AddMessage(f'Site status: {site_status}')
        arcpy.AddMessage(f'Start date: {start_dt}')
        arcpy.AddMessage(f'End date: {end_dt}')
        arcpy.AddMessage(f'Clip: {clip}')
        arcpy.AddMessage(f'Overwrite: {overwrite}')
        usgs_gages.get_usgs_gages(extent, out_features, overwrite, clip, usgs_gages.UsgsSiteStatus(site_status),
                                  start_dt=start_dt.date(), end_dt=end_dt.date())
