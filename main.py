from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import geopandas as gpd
import tempfile
import os
import zipfile

app = FastAPI(title="ParcelasYA Converter", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/convert")
async def convert_geojson(
    formato: str = Form(..., regex="^(kml|shp|gpkg)$"),
    file: UploadFile = File(...)
):
    # Guardar el archivo temporalmente
    with tempfile.TemporaryDirectory() as tmpdir:
        geojson_path = os.path.join(tmpdir, "parcela.geojson")
        with open(geojson_path, "wb") as f:
            f.write(await file.read())

        gdf = gpd.read_file(geojson_path)

        if formato == "kml":
            out_path = os.path.join(tmpdir, "parcela.kml")
            gdf.to_file(out_path, driver="KML")
            return FileResponse(out_path, filename="parcela.kml", media_type="application/vnd.google-earth.kml+xml")

        elif formato == "gpkg":
            out_path = os.path.join(tmpdir, "parcela.gpkg")
            gdf.to_file(out_path, driver="GPKG")
            return FileResponse(out_path, filename="parcela.gpkg", media_type="application/geopackage+sqlite3")

        elif formato == "shp":
            shp_dir = os.path.join(tmpdir, "shp")
            os.makedirs(shp_dir, exist_ok=True)
            shp_path = os.path.join(shp_dir, "parcela.shp")
            gdf.to_file(shp_path, driver="ESRI Shapefile")
            # Empaquetar en ZIP
            zip_path = os.path.join(tmpdir, "parcela_shp.zip")
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
                    fpath = shp_path.replace(".shp", ext)
                    if os.path.exists(fpath):
                        zipf.write(fpath, os.path.basename(fpath))
            return FileResponse(zip_path, filename="parcela_shp.zip", media_type="application/zip")

    return JSONResponse({"error": "Formato no soportado"}, status_code=400)

@app.get("/")
def root():
    return {"message": "ParcelasYA Converter API"}
