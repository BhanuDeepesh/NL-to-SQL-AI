from fastapi import FastAPI, UploadFile, File, Form
from schema_system import SmartSchemaSystem, SchemaFormat
import tempfile

app = FastAPI()

@app.post("/api/process-schema")
async def process_schema(
    file: UploadFile = File(...),
    query: str = Form(...),
    output_format: str = Form("json"),
    threshold: float = Form(0.1)
):
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # Process schema
        system = SmartSchemaSystem(relevance_threshold=threshold)
        result = system.process_schema(
            input_path=temp_path,
            query=query,
            output_format=SchemaFormat[output_format.upper()]
        )

        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}