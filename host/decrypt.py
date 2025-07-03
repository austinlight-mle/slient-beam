import os
import pyzipper

ENCRYPTED_ZIP = "screenshots_secure.zip"
OUTPUT_DIR = "decrypted_images"
PASSWORD = os.getenv("ZIP_ENCRYPTION_KEY", "defaultpassword").encode()

os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_to_folder():
    with pyzipper.AESZipFile(ENCRYPTED_ZIP, "r") as archive:
        archive.setpassword(PASSWORD)
        for name in archive.namelist():
            data = archive.read(name)
            with open(os.path.join(OUTPUT_DIR, name), "wb") as f:
                f.write(data)
            print(f"Extracted {name}")


if __name__ == "__main__":
    extract_to_folder()
