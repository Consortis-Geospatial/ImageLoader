from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit,
    QPushButton, QFileDialog, QLabel, QMessageBox, QAction
)
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.core import QgsProject, QgsWkbTypes, QgsRasterLayer, QgsMapLayer
from qgis.gui import QgsMapTool, QgsMapToolIdentifyFeature, QgsRubberBand
from qgis.PyQt.QtGui import QCursor, QIcon, QPixmap, QColor
import glob
import os

class ImageLoaderDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.setWindowTitle("Image Loader Settings")
        self.current_tool = None
        self.timer = None

        # Layout
        layout = QVBoxLayout()

        # Layer selection
        layer_layout = QHBoxLayout()
        layer_layout.addWidget(QLabel("Layer containing the raster's name/code:"))
        self.layerCombo = QComboBox()
        layer_layout.addWidget(self.layerCombo)
        layout.addLayout(layer_layout)

        # Field selection
        field_layout = QHBoxLayout()
        field_layout.addWidget(QLabel("Field that contains the name/code:"))
        self.fieldCombo = QComboBox()
        field_layout.addWidget(self.fieldCombo)
        layout.addLayout(field_layout)

        # Folder selection
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Raster's folder:"))
        self.folderEdit = QLineEdit()
        self.browseBtn = QPushButton("...")
        self.browseBtn.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folderEdit)
        folder_layout.addWidget(self.browseBtn)
        layout.addLayout(folder_layout)

        # Prefix selection
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("Filename Prefix (optional):"))
        self.prefixEdit = QLineEdit()
        prefix_layout.addWidget(self.prefixEdit)
        layout.addLayout(prefix_layout)

        # Suffix selection
        suffix_layout = QHBoxLayout()
        suffix_layout.addWidget(QLabel("Filename Suffix (optional):"))
        self.suffixEdit = QLineEdit()
        suffix_layout.addWidget(self.suffixEdit)
        layout.addLayout(suffix_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.applyBtn = QPushButton("Activate")
        self.applyBtn.clicked.connect(self.apply_settings)
        self.cancelBtn = QPushButton("Cancel")
        self.cancelBtn.clicked.connect(self.reject)
        button_layout.addWidget(self.applyBtn)
        button_layout.addWidget(self.cancelBtn)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.populate_layers()
        self.layerCombo.currentIndexChanged.connect(self.populate_fields)

    def populate_layers(self):
        self.layerCombo.clear()
        self.layer_map = {}
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == layer.VectorLayer and layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                self.layer_map[layer.name()] = layer
                self.layerCombo.addItem(layer.name())
        self.populate_fields()

    def populate_fields(self):
        self.fieldCombo.clear()
        layer = self.get_selected_layer()
        if layer:
            field_names = [field.name() for field in layer.fields()]
            self.fieldCombo.addItems(field_names)
            print(f"Populated fields for layer {layer.name()}: {field_names}")

    def get_selected_layer(self):
        layer_name = self.layerCombo.currentText()
        return self.layer_map.get(layer_name)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folderEdit.setText(folder)

    def apply_settings(self):
        layer = self.get_selected_layer()
        field = self.fieldCombo.currentText()
        folder = self.folderEdit.text()
        prefix = self.prefixEdit.text().strip()
        suffix = self.suffixEdit.text().strip()

        if not layer:
            QMessageBox.warning(self, "Missing Input", "Please select a valid polygon layer.")
            print("No polygon layer selected.")
            return
        if not field:
            QMessageBox.warning(self, "Missing Input", "Please choose a field that contains the raster name/code.")
            print("No field selected.")
            return
        if not folder or not os.path.isdir(folder):
            QMessageBox.warning(self, "Missing Input", "Please select a valid folder containing the raster images.")
            print("Invalid folder selected.")
            return

        # Validate field
        field_names = [field.name() for field in layer.fields()]
        if field not in field_names:
            QMessageBox.warning(self, "Field Not Found", f"The field '{field}' was not found in the selected layer. Available fields: {field_names}")
            print(f"The field '{field}' was not found in the selected layer. Available fields: {field_names}")
            return

        # Ensure layer is active and visible
        QgsProject.instance().layerTreeRoot().findLayer(layer.id()).setItemVisibilityChecked(True)
        self.iface.setActiveLayer(layer)
        print(f"Layer {layer.name()} set as active and visible")

        # Ensure no other map tool is active
        if self.canvas.mapTool():
            self.canvas.unsetMapTool(self.canvas.mapTool())
            print("Unset existing map tool")

        # Activate map tool
        try:
            self.current_tool = CustomIdentifyTool(self.canvas, layer, field, folder, prefix, suffix, self.iface)
            self.canvas.setMapTool(self.current_tool)
            self.canvas.setFocus()
            self.canvas.refresh()
            print(f"Map tool set for layer: {layer.name()}, field: {field}, folder: {folder}, prefix: {prefix}, suffix: {suffix}")
            print(f"Current map tool: {self.canvas.mapTool()}")

            # Monitor map tool changes
            self.canvas.mapToolSet.connect(self.on_map_tool_changed)
            self.timer = QTimer()
            self.timer.timeout.connect(self.check_map_tool)
            self.timer.start(1000)

            self.iface.messageBar().pushInfo("Image Loader", "Tool activated. Click a polygon to load its associated raster image(s). Press Esc to deactivate.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize map tool: {str(e)}")
            print(f"Failed to initialize map tool: {str(e)}")

    def on_map_tool_changed(self, new_tool, old_tool):
        if new_tool != self.current_tool and self.current_tool:
            print(f"Map tool changed to {new_tool}. Deactivating Image Loader tool.")
            self.current_tool = None
            if self.timer:
                self.timer.stop()
                self.timer = None
            self.canvas.setCursor(QCursor(Qt.ArrowCursor))

    def check_map_tool(self):
        if self.current_tool and self.canvas.mapTool() != self.current_tool:
            print("Map tool unset, reapplying")
            self.canvas.setMapTool(self.current_tool)
            self.canvas.setFocus()
            self.canvas.refresh()
            print(f"Reapplied map tool: {self.canvas.mapTool()}")

class CustomIdentifyTool(QgsMapTool):
    def __init__(self, canvas, layer, field_name, folder, prefix, suffix, iface):
        super().__init__(canvas)
        self.canvas = canvas
        self.layer = layer
        self.field_name = field_name
        self.folder = folder
        self.prefix = prefix
        self.suffix = suffix
        self.iface = iface
        self.rubber_band = None
        try:
            self.identify_tool = QgsMapToolIdentifyFeature(canvas)
            self.identify_tool.setLayer(layer)
            print(f"CustomIdentifyTool initialized for layer: {layer.name()}, field: {field_name}, prefix: {prefix}, suffix: {suffix}")
            print(f"Layer active: {self.iface.activeLayer() == layer}, Visible: {QgsProject.instance().layerTreeRoot().findLayer(layer.id()).isVisible()}")
            # Load custom cursor with centered hotspot
            cursor_path = os.path.join(os.path.dirname(__file__), 'cursor.png')
            if os.path.exists(cursor_path):
                pixmap = QPixmap(cursor_path)
                if not pixmap.isNull() and pixmap.width() == 32 and pixmap.height() == 32:
                    self.setCursor(QCursor(pixmap, 16, 16))  # Center hotspot at (16, 16)
                    print("Custom cursor loaded from cursor.png with centered hotspot")
                else:
                    print("Invalid cursor.png: Must be a 32x32 pixel image")
                    self.setCursor(QCursor(Qt.CrossCursor))
            else:
                print("cursor.png not found in plugin folder")
                self.setCursor(QCursor(Qt.CrossCursor))
        except Exception as e:
            print(f"Error initializing QgsMapToolIdentifyFeature or cursor: {str(e)}")
            self.iface.messageBar().pushCritical("Image Loader", f"Error initializing tool or cursor: {str(e)}")
            self.setCursor(QCursor(Qt.CrossCursor))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            print("Tool deactivated (Esc key pressed).")
            self.canvas.unsetMapTool(self)
            self.canvas.setCursor(QCursor(Qt.ArrowCursor))
            # Signal to ImageLoaderDialog to clean up
            self.canvas.mapToolSet.emit(None, self)

    def canvasReleaseEvent(self, event):
        try:
            results = self.identify_tool.identify(event.x(), event.y(), [self.layer], self.identify_tool.TopDownStopAtFirst)
            print(f"Identify results: {results}")
            if not results:
                self.iface.messageBar().pushWarning("Image Loader", "No polygon feature was identified. Make sure the correct layer is active and visible. Ensure the correct layer is active and visible.")
                print("No polygon feature was identified. Make sure the correct layer is active and visible.")
                return

            feature = results[0].mFeature
            print(f"Feature identified: {feature.id()}, Attributes: {feature.attributes()}")
            # Highlight the feature with a red rubberband
            try:
                self.highlight_feature(feature)
            except Exception as e:
                print(f"Error highlighting feature: {str(e)}")
                self.iface.messageBar().pushWarning("Image Loader", f"Failed to highlight feature: {str(e)}")
            # Continue with image loading even if highlighting fails
            self.load_image(feature)
        except Exception as e:
            self.iface.messageBar().pushWarning("Image Loader", f"Error identifying feature: {str(e)}")
            print(f"Error identifying feature: {str(e)}")

    def highlight_feature(self, feature):
        if self.rubber_band:
            self.canvas.scene().removeItem(self.rubber_band)
            self.rubber_band = None
        self.rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rubber_band.setColor(QColor(255, 0, 0))  # Red
        self.rubber_band.setWidth(2)
        self.rubber_band.setToGeometry(feature.geometry(), self.layer)  # Use setToGeometry
        self.rubber_band.show()
        print("Highlighted feature with red rubberband")
        QTimer.singleShot(100, self.remove_rubber_band)  # Remove after 0.1 seconds

    def remove_rubber_band(self):
        if self.rubber_band:
            self.canvas.scene().removeItem(self.rubber_band)
            self.rubber_band = None
            self.canvas.refresh()
            print("Removed rubberband highlight")

    def load_image(self, feature):
        field_names = [field.name() for field in self.layer.fields()]
        print(f"Available fields in layer: {field_names}")
        print(f"Attempting to access field: '{self.field_name}'")

        try:
            code = str(feature[self.field_name]).strip()
            print(f"Feature code: {code}")
        except KeyError as e:
            self.iface.messageBar().pushWarning("Image Loader", f"KeyError accessing field '{self.field_name}'. Attributes: {feature.attributes()}")
            print(f"KeyError accessing field '{self.field_name}'. Attributes: {feature.attributes()}")
            field_index = self.layer.fields().indexFromName(self.field_name)
            print(f"Field index for '{self.field_name}': {field_index}")
            if field_index != -1:
                code = str(feature.attributes()[field_index]).strip()
                print(f"Feature code (via index): {code}")
            else:
                self.iface.messageBar().pushWarning("Image Loader", f"Field index for '{self.field_name}' not found.")
                print(f"Field index for '{self.field_name}' not found.")
                return

        if not code:
            self.iface.messageBar().pushWarning("Image Loader", "The selected feature has no value in the target field.")
            print("The selected feature has no value in the target field.")
            return

        search_name = code
        self.iface.messageBar().pushInfo("Image Loader", f"Searching for images: {search_name}")
        print(f"Searching for images: {search_name}")

        image_extensions = ['.tif', '.tiff', '.jp2', '.jpeg', '.jpg', '.png']
        matches = []
        for ext in image_extensions:
            # Construct pattern with prefix and suffix
            pattern = os.path.join(self.folder, f"{self.prefix}*{search_name}*{self.suffix}{ext}")
            print(f"Searching pattern: {pattern}")
            matches.extend(glob.glob(pattern))

        print(f"Matches found: {matches}")
        if not matches:
            self.iface.messageBar().pushWarning("Image Loader", f"No matching images found for name/code: {search_name}")
            print(f"No matching images found for name/code: {search_name}")
            return

        loaded_images = []
        for image_path in matches:
            print(f"Loading image: {image_path}")
            # Use the file name without extension as the layer name to avoid duplicates
            layer_name = os.path.splitext(os.path.basename(image_path))[0] + "_" + os.path.splitext(image_path)[1][1:]
            raster_layer = QgsRasterLayer(image_path, layer_name)
            if not raster_layer.isValid():
                self.iface.messageBar().pushWarning("Image Loader", f"Failed to load image file: {image_path}")
                print(f"Failed to load image file: {image_path}")
                continue
            QgsProject.instance().addMapLayer(raster_layer)
            loaded_images.append(layer_name)

        if loaded_images:
            self.canvas.refresh()
            self.iface.messageBar().pushInfo("Image Loader", f"Loaded images: {', '.join(loaded_images)}")
            print(f"Loaded images: {', '.join(loaded_images)}")
        else:
            self.iface.messageBar().pushWarning("Image Loader", f"No valid images could be loaded for name/code: {search_name}")
            print(f"No valid images could be loaded for name/code: {search_name}")

class ImageLoaderPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.current_tool = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        self.action = QAction(QIcon(icon_path), "Image Loader", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Image Loader", self.action)
        print("Image Loader plugin initialized")

    def unload(self):
        if self.current_tool:
            self.iface.mapCanvas().unsetMapTool(self.current_tool)
        self.iface.removePluginMenu("&Image Loader", self.action)
        self.iface.removeToolBarIcon(self.action)
        print("Image Loader plugin unloaded")

    def run(self):
        dialog = ImageLoaderDialog(self.iface, self.iface.mainWindow())
        dialog.exec_()