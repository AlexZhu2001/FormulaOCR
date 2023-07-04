import binascii
from io import BytesIO
from pix2tex.cli import LatexOCR
from fastapi import FastAPI, HTTPException
from typing import Union
import uvicorn
from PIL import Image
import latex2mathml.converter
from pydantic import BaseModel
import rsa
import base64
import lzma

BLOCK_SIZE = 128

app = FastAPI(debug=True)
model: Union[None, LatexOCR] = None
private_key: Union[None, str] = None


class Item(BaseModel):
    img: str


class OutModel(BaseModel):
    tex: str
    mml: str


@app.on_event("startup")
def init_setup():
    global model
    global private_key
    global decoder
    model = LatexOCR()
    with open("rsa_private_key.pem") as f:
        private_key = f.read()
    private_key = rsa.PrivateKey.load_pkcs1(private_key)


@app.get("/")
def health_check():
    resp = {
        "code": 0,
        "msg": "Success",
    }
    return resp


@app.post("/predict", response_model=OutModel)
def predict(item: Item):
    global private_key, model
    try:
        img = base64.b64decode(item.img)
        dec = []
        for i in range(0, len(img), BLOCK_SIZE):
            b = img[i : i + BLOCK_SIZE]
            dec.append(rsa.decrypt(b, private_key))
        img = bytes().join(dec)
        print(img)
        img = lzma.decompress(img)
        img = Image.open(BytesIO(img))
        tex, mml = img2formula(img)
    except binascii.Error as e:
        raise HTTPException(status_code=500, detail=f"Base64 decode error: {e}")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"RSA decrypt error: {e}")
    except TypeError as e:
        raise HTTPException(status_code=500, detail=f"RSA decrypt error: {e}")
    except lzma.LZMAError as e:
        raise HTTPException(status_code=500, detail=f"lzma decompress error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
    return OutModel(tex=tex, mml=mml)


def img2formula(img: Image.Image) -> tuple[str, str]:
    global model
    tex = model(img)
    mml = latex2mathml.converter.convert(tex)
    return tex, mml


if __name__ == "__main__":
    uvicorn.run(app, port=8502)
