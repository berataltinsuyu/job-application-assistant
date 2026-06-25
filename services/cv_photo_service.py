from io import BytesIO

from PIL import Image, ImageOps


def prepare_cv_photo_for_export(photo_bytes: bytes, size_px: int = 512) -> bytes:
    """Center-crop uploaded CV photos to a square PNG without distorting aspect ratio."""
    if not photo_bytes:
        return b""

    with Image.open(BytesIO(photo_bytes)) as image:
        image = ImageOps.exif_transpose(image)
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGB")

        width, height = image.size
        crop_size = min(width, height)
        left = max(0, (width - crop_size) // 2)
        top = max(0, (height - crop_size) // 2)
        image = image.crop((left, top, left + crop_size, top + crop_size))
        resample = getattr(Image.Resampling, "LANCZOS", Image.LANCZOS)
        image = image.resize((size_px, size_px), resample)

        output = BytesIO()
        image.save(output, format="PNG", optimize=True)
        return output.getvalue()
