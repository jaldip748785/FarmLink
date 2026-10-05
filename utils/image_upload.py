import os

from werkzeug.utils import secure_filename

from utils.helpers import allowed_file
from utils.helpers import generate_filename


UPLOAD_FOLDER = "static/uploads/products"


def save_product_image(file):

    """
    Save uploaded product image.
    """

    if file.filename == "":
        return None

    if not allowed_file(file.filename):
        return None

    filename = secure_filename(file.filename)

    filename = generate_filename(filename)

    file.save(os.path.join(UPLOAD_FOLDER, filename))

    return filename


PROFILE_FOLDER = "static/uploads/profiles"


def save_profile_image(file):

    """
    Save uploaded profile image.
    """

    if file.filename == "":
        return None

    if not allowed_file(file.filename):
        return None

    filename = secure_filename(file.filename)

    filename = generate_filename(filename)

    file.save(os.path.join(PROFILE_FOLDER, filename))

    return filename