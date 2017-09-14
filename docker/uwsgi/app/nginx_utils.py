import mimetypes
import os
import werkzeug
from flask import safe_join, abort


def send_xaccel_dir(app, directory: str, filename: str, xsendfile_path: str, **opts):
    """
    Resource can be served directly by nginx by sending X-Accel-Redirect header
        from Flask.
    Params:
        directory (str):    directory the file is in
        filename (str):     actual file name
        xsendfile_path(str):nginx path to be used for constructing the resource path
    """
    path = safe_join(directory, filename)
    if not os.path.isfile(path):
        abort(404)

    mime_type = (mimetypes.guess_type(filename, strict=False)[0] or
                 "application/octet-stream")
    headers = werkzeug.datastructures.Headers()
    headers["X-Accel-Redirect"] = safe_join(xsendfile_path, filename)

    return app.response_class(None, mimetype=mime_type, headers=headers, **opts)
