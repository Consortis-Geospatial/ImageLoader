def classFactory(iface):
    from .image_loader import ImageLoaderPlugin
    return ImageLoaderPlugin(iface)