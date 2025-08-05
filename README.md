<div align=center>
  <img width="64" height="64" alt="icon" src="https://github.com/user-attachments/assets/3eae6a55-6e1d-40ad-b38d-471ff595270d" />
</div>

# ImageLoader
**ImageLoader** is a QGIS plugin that allows users to click on polygons (e.g., grid tiles) to automatically load and display associated raster images from a local folder. The plugin supports customizable filename patterns using prefixes and suffixes, and provides an interactive interface for selecting the input layer, field, and image directory.

---

## Features

- Click a polygon on the QGIS map canvas to load corresponding raster images based on a specified field value.
- Support for customizable filename patterns with optional prefix and suffix inputs.
- Interactive dialog to select a polygon layer, field containing the raster name/code, and image folder.
- Visual feedback with a temporary red rubber band highlighting the clicked polygon.
- Custom cursor (32x32 pixel `cursor.png`) for precise clicking, with fallback to a cross cursor.
- Supports common raster formats (`.tif`, `.tiff`, `.jp2`, `.jpeg`, `.jpg`, `.png`).
- Error handling for invalid layers, fields, or folders with user-friendly messages.

### Example Use Case
If your raster folder contains files like:
- `ortho_999999.jp2`
- `ortho_999998.tiff`
- `ortho_999997.tif`

And your polygon layer has a field `tile_code` with values `999999`, `999998`, `999997`, you can set:
- **Prefix**: `ortho_`
- **Suffix**: leave it blank

Then, clicking on a tile will load the matching raster (e.g., `ortho_999999.jp2`) directly into QGIS.

You can set Prefix or Suffix or both Prefix and Suffix or leave it blank (e.g., `ortho_999999_georef.jp2`, or `999998_ortho.tiff`, or `999997.png`).

---

## How It Works

1. Activate the plugin via the toolbar icon or the "Image Loader" menu to open the settings dialog.
2. Select a polygon layer containing the grid cells.
3. Choose the field that contains the raster name or code.
4. Specify the folder containing the raster images and optional filename prefix/suffix.
5. Click "Activate" to enable the map tool.
6. Click a polygon on the map canvas to load associated raster images, with a temporary red highlight on the selected polygon.
7. Press Esc to deactivate the tool.

---

## Installation

1. Clone or download this repository:
   ```bash
   git clone https://github.com/Consortis-Geospatial/ImageLoader.git
   ```
2. Copy the folder to your QGIS plugin directory:
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - Windows: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
3. Ensure the `cursor.png` (32x32 pixel image) is included in the plugin folder for the custom cursor.
4. Open QGIS and enable the plugin via Plugins > Manage and Install Plugins.

---

## Screenshot
Coming Soon...

---

## Developer Notes

- Developed in Python using PyQt and PyQGIS APIs.
- Uses a custom `QDialog` for configuring layer, field, folder, and filename patterns.
- Employs a custom `QgsMapTool` based on `QgsMapToolIdentifyFeature` to handle polygon clicks and load rasters.
- Temporary red `QgsRubberBand` visualization for 100ms to highlight selected polygons.
- Supports raster loading with `QgsRasterLayer` and filename pattern matching via `glob`.
- Includes robust error handling for invalid inputs, missing files, or layer issues.
- Compatible with QGIS 3.0 and later.

---

## Dependencies

- **QGIS 3.x**: Compatible with QGIS version 3.0 and later (tested with 3.38.3), providing the core GIS functionality and PyQGIS API.
- **Python 3**: QGIS 3.x includes an embedded Python 3 interpreter (typically version 3.7 or higher).
- **PyQt5**: Required for GUI components like `QDialog`, `QComboBox`, `QLineEdit`, `QPushButton`, `QLabel`, `QFileDialog`, and `QMessageBox`. Bundled with QGIS 3.x installations (version 5.15.10 or similar).
- **PyQGIS**: Provides core QGIS functionality, including `QgsProject`, `QgsRasterLayer`, `QgsMapTool`, `QgsMapToolIdentifyFeature`, and `QgsRubberBand`. Included with QGIS.
- **PyQt5-sip**: A dependency for PyQt5, typically included with QGIS (version 12.13.0 or higher).
- **Python Standard Library**:
  - `os`: For handling file paths and folder operations.
  - `glob`: For matching raster filenames with user-defined patterns.

---

## Support and Contributions

- **Homepage**: [https://github.com/Consortis-Geospatial](https://github.com/Consortis-Geospatial)
- **Issue Tracker**: [https://github.com/Consortis-Geospatial/ImageLoader/issues](https://github.com/Consortis-Geospatial/ImageLoader/issues)
- **Author**: Gkaravelis Andreas - Consortis Geospatial
- **Email**: gkaravelis@consortis.gr
- **Repository**: [https://github.com/Consortis-Geospatial/ImageLoader](https://github.com/Consortis-Geospatial/ImageLoader)

---

## License
This plugin is released under the GPL-3.0 license.

<div align=center>
  <img width="64" height="64" alt="icon" src="https://github.com/user-attachments/assets/3eae6a55-6e1d-40ad-b38d-471ff595270d" />
</div>
