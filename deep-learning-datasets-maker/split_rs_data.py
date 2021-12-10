# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SplitRSData
                                 A QGIS plugin
 tools to handle raster and vector data to split it into small pieces equaled in size for machine learning datasets
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-12-08
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Youssef Harby
        email                : youssef_harby@yahoo.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog
from qgis.core import (QgsMapLayerProxyModel, QgsProject, QgsProcessingFeedback, QgsMessageLog, Qgis)
# import processing, tempfile
import math
import os.path as osp

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .split_rs_data_dialog import SplitRSDataDialog
import os.path
from osgeo import gdal, ogr
from qgis.utils import iface


class SplitRSData:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SplitRSData_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Deep Learning Datasets Maker')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SplitRSData', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/split_rs_data/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Deep Learning Datasets Maker'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Deep Learning Datasets Maker'),
                action)
            self.iface.removeToolBarIcon(action)

    def select_output_rasterize(self):
        filenameVR, _filter = QFileDialog.getSaveFileName(self.dlg, "Select Output Rasterized File","",'*.tif')
        self.dlg.lineEditV_R.setText(filenameVR)
    def select_output_images(self):
        # filenameIM, _filter = QFileDialog.getSaveFileName(self.dlg, "Select Output Images Files","",'*.jpg') 
        filenameIM = QFileDialog.getExistingDirectory(self.dlg, 'Select Empty Folder For Images')
        self.dlg.lineEditImages.setText(filenameIM)
    def select_output_labels(self):
        # filenameLB, _filter = QFileDialog.getSaveFileName(self.dlg, "Select Output Labels Files","",'*.png')
        filenameLB = QFileDialog.getExistingDirectory(self.dlg, 'Select Empty Folder For Labels')
        self.dlg.lineEditLabels.setText(filenameLB)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = SplitRSDataDialog()
            self.dlg.pushButtonVR.clicked.connect(self.select_output_rasterize)
            self.dlg.pushButtonImg.clicked.connect(self.select_output_images)
            self.dlg.pushButtonLabl.clicked.connect(self.select_output_labels)
        
        # Fetch the currently loaded layers
        # Populate the comboBox with names of all the loaded layers
        self.dlg.mMapLayerComboBoxR.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.dlg.mMapLayerComboBoxV.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.dlg.comboBoxImgSize.clear()
        self.dlg.comboBoxImgSize.addItems(["64", "128", "256", "512", "1024"])
        self.dlg.comboBoxImgSize.setCurrentIndex(3)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            currentrasterlay = self.dlg.mMapLayerComboBoxR.currentText() # Get the selected raster layer
            rlayers = QgsProject.instance().mapLayersByName(currentrasterlay)
            fn_ras = rlayers[0]
            currentvectorlay = self.dlg.mMapLayerComboBoxV.currentText() # Get the selected raster layer
            vlayers = QgsProject.instance().mapLayersByName(currentvectorlay)
            fn_vec = vlayers[0]
            # ttt = (tempfile.NamedTemporaryFile(suffix='.shp'))
            output = str(self.dlg.lineEditV_R.text())

            # Log for files
            feedback = QgsProcessingFeedback()
            feedback.pushInfo(str(fn_ras.dataProvider().dataSourceUri()))
            feedback.pushInfo(str(fn_vec.dataProvider().dataSourceUri()))
            feedback.pushInfo(output)

            # iface.messageBar().pushMessage(output, level=Qgis.Critical)
            def rasterize(fn_ras, fn_vec, output):
                driver = ogr.GetDriverByName("ESRI Shapefile")
                ras_ds = gdal.Open(fn_ras.dataProvider().dataSourceUri())
                vec_ds = driver.Open(fn_vec.dataProvider().dataSourceUri(), 1)

                lyr = vec_ds.GetLayer()
                geot = ras_ds.GetGeoTransform()
                proj = ras_ds.GetProjection()  # Get the projection from original tiff (fn_ras)

                layerdefinition = lyr.GetLayerDefn()
                feature = ogr.Feature(layerdefinition)

                schema = []
                for n in range(layerdefinition.GetFieldCount()):
                    fdefn = layerdefinition.GetFieldDefn(n)
                    schema.append(fdefn.name)
                yy = feature.GetFieldIndex("MLDS")
                if yy < 0:
                    print("MLDS field not found, we will create one for you and make all values to 1")
                else:
                    lyr.DeleteField(yy)
                    # lyr.ResetReading()
                new_field = ogr.FieldDefn("MLDS", ogr.OFTInteger)
                lyr.CreateField(new_field)
                for feature in lyr:
                    feature.SetField("MLDS", 1)
                    lyr.SetFeature(feature)
                    feature = None

                # isAttributeOn = att_field_input if att_field_input != '' else first_att_field
                # pixelsizeX = 0.2 if ras_ds.RasterXSize < 0.2 else ras_ds.RasterXSize
                # pixelsizeY = -0.2 if ras_ds.RasterYSize < -0.2 else ras_ds.RasterYSize

                drv_tiff = gdal.GetDriverByName("GTiff")
                chn_ras_ds = drv_tiff.Create(
                    output, ras_ds.RasterXSize, ras_ds.RasterYSize, 1, gdal.GDT_Byte)
                
                # Set the projection from original tiff (fn_ras) to the rasterized tiff
                chn_ras_ds.SetGeoTransform(geot)
                chn_ras_ds.SetProjection(proj)
                chn_ras_ds.FlushCache()

                gdal.RasterizeLayer(chn_ras_ds, [1], lyr, burn_values=[1], options=["ATTRIBUTE=MLDS"])

                # Change No Data Value to 0
                # chn_ras_ds.GetRasterBand(1).SetNoDataValue(0)
                chn_ras_ds = None
                # lyr.DeleteField(yy) # delete field
                vec_ds = None
            rasterize(fn_ras, fn_vec, output)
            iface.messageBar().pushMessage("You will find the rasterized file in " + output, level=Qgis.Info, duration=5)
            iface.addRasterLayer(output, "0 1 class")

            # Start Splitting 
            def mygridfun(fn_ras, cdpath, frmt_ext, imgfrmat, scaleoptions, needed_out_x, needed_out_y, file_name):
                ds = gdal.Open(fn_ras)
                gt = ds.GetGeoTransform()

                # get coordinates of upper left corner
                xmin = gt[0]
                ymax = gt[3]
                resx = gt[1]
                res_y = gt[5]
                resy = abs(res_y)

                # round up to nearst int
                xnotround = ds.RasterXSize / needed_out_x
                xround = math.ceil(xnotround)
                ynotround = ds.RasterYSize / needed_out_y
                yround = math.ceil(ynotround)

                # pixel to meter - 512×10×0.18
                pixtomX = needed_out_x * xround * resx
                pixtomy = needed_out_y * yround * resy
                # size of a single tile
                xsize = pixtomX / xround
                ysize = pixtomy / yround
                # create lists of x and y coordinates
                xsteps = [xmin + xsize * i for i in range(xround + 1)]
                ysteps = [ymax - ysize * i for i in range(yround + 1)]

                # loop over min and max x and y coordinates
                for i in range(xround):
                    for j in range(yround):
                        xmin = xsteps[i]
                        xmax = xsteps[i + 1]
                        ymax = ysteps[j]
                        ymin = ysteps[j + 1]

                        # use gdal warp
                        # gdal.WarpOptions(outputType=gdal.gdalconst.GDT_Byte)
                        # gdal.Warp("ds"+str(i)+str(j)+".tif", ds,
                        # outputBounds = (xmin, ymin, xmax, ymax), dstNodata = -9999)

                        # or gdal translate to subset the input raster
                        gdal.Translate(osp.join(cdpath,  \
                                                (str(file_name) + "-" + str(j) + "-" + str(i) + "." + frmt_ext)), 
                                    ds, 
                                    projWin=(abs(xmin), abs(ymax), abs(xmax), abs(ymin)),
                                    xRes=resx, 
                                    yRes=-resy, 
                                    outputType=gdal.gdalconst.GDT_Byte, 
                                    format=imgfrmat, 
                                    scaleParams=[[scaleoptions]])

            # close the open dataset!!!
            # ds = None

            # feedback.pushInfo(str(fn_ras.dataProvider().dataSourceUri()))
            # feedback.pushInfo(str(fn_vec.dataProvider().dataSourceUri()))
            #do it 
            image_folder_path = str(self.dlg.lineEditImages.text())
            label_folder_path = str(self.dlg.lineEditLabels.text())
            gggg = fn_ras.dataProvider().dataSourceUri()
            mygridfun(gggg, image_folder_path, "jpg", "JPEG", "", 512, 512, currentrasterlay)
            mygridfun(output, label_folder_path, "png", "PNG", "", 512, 512, currentvectorlay)
            iface.messageBar().pushMessage("You will find the dataset in " + image_folder_path, level=Qgis.Success, duration=5)