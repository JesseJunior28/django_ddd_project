from pathlib import Path
from uuid import uuid4


class LocalProductStorage:
    allowed_extensions = {".jpg", ".jpeg", ".png"}
    allowed_mime_types = {"image/jpeg", "image/png"}
    max_size = 5 * 1024 * 1024

    def __init__(self, directory="/tmp/django-product-uploads"):
        self.directory = Path(directory)

    def save(self, uploaded):
        suffix = Path(uploaded.name).suffix.lower()
        if uploaded.content_type not in self.allowed_mime_types:
            raise ValueError("O tipo MIME deve ser uma imagem (image/jpeg, image/png)")
        if suffix not in self.allowed_extensions:
            raise ValueError("A extensão do arquivo deve ser uma das seguintes: .jpg, .jpeg, .png")
        if not uploaded.size or uploaded.size > self.max_size:
            raise ValueError("O tamanho máximo para o arquivo é 5Mb.")
        self.directory.mkdir(parents=True, exist_ok=True)
        name = f"{uuid4()}{suffix}"
        (self.directory / name).write_bytes(uploaded.read())
        return name

    def delete(self, name):
        (self.directory / name).unlink(missing_ok=True)
