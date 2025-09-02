from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
import shutil
from pathlib import Path
import tempfile

# Import our banana.py functions
from banana import analyze_clothing, generate, ClothingAnalysis

app = FastAPI(title="Banana Product Listing API", version="1.0.0")

# Configure CORS to allow localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories if they don't exist
UPLOAD_DIR = Path("temp_uploads")
OUTPUT_DIR = Path("output")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Mount static files to serve generated images
app.mount("/images", StaticFiles(directory="output"), name="images")

# Response models
class ProductListingResponse(BaseModel):
    success: bool
    message: str
    clothing_analysis: Optional[ClothingAnalysis] = None
    generated_image_url: Optional[str] = None
    generated_image_path: Optional[str] = None

class ErrorResponse(BaseModel):
    success: bool
    error: str
    detail: Optional[str] = None

# Utility functions
def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
    """Save uploaded file to destination"""
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()

def validate_image_file(file: UploadFile) -> bool:
    """Validate that uploaded file is an image"""
    if not file.content_type or not file.content_type.startswith('image/'):
        return False
    
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    file_extension = Path(file.filename).suffix.lower()
    return file_extension in allowed_extensions

def cleanup_temp_files(*file_paths: Path) -> None:
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            print(f"Warning: Could not delete temp file {file_path}: {e}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Banana Product Listing API is running!", "status": "healthy"}

@app.post("/generate-simple", response_model=ProductListingResponse)
async def generate_simple_listing(
    output_filename: Optional[str] = None
):
    """
    Simple endpoint that uses the default images from clothes/ and model/ folders.
    No file uploads needed - just a simple POST request!
    """
    
    # Use default images
    clothing_path = "clothes/IMG_7277.jpeg"
    model_path = "model/ImageCrocPrototype.jpeg"
    
    # Generate output filename
    if not output_filename:
        import uuid
        output_filename = f"simple_listing_{str(uuid.uuid4())[:8]}.png"
    elif not output_filename.endswith(('.png', '.jpg', '.jpeg')):
        output_filename += ".png"
    
    output_path = OUTPUT_DIR / output_filename
    
    try:
        # Step 1: Analyze the clothing item
        try:
            clothing_analysis = analyze_clothing(clothing_path)
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to analyze clothing item: {str(e)}"
            )
        
        # Step 2: Generate the product listing image
        try:
            success = generate(clothing_path, model_path, str(output_path))
            
            if not success:
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to generate product listing image"
                )
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to generate product listing: {str(e)}"
            )
        
        # Generate image URL for frontend access
        image_url = f"/images/{output_filename}"
        
        return ProductListingResponse(
            success=True,
            message="Product listing generated successfully!",
            clothing_analysis=clothing_analysis,
            generated_image_url=image_url,
            generated_image_path=str(output_path)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected error: {str(e)}"
        )


@app.post("/generate-product-listing", response_model=ProductListingResponse)
async def generate_product_listing(
    clothing_image: UploadFile = File(..., description="Image of the clothing item"),
    model_image: UploadFile = File(..., description="Image of the model"),
    output_filename: Optional[str] = Form(None, description="Optional custom output filename")
):
    """
    Generate a product listing image showing a model wearing the clothing item.
    
    This endpoint:
    1. Analyzes the clothing item to extract description and tags
    2. Generates a 4-angle product listing image
    3. Returns structured analysis results and image URL
    """
    
    # Validate uploaded files
    if not validate_image_file(clothing_image):
        raise HTTPException(
            status_code=400, 
            detail="Clothing image must be a valid image file (jpg, jpeg, png, gif, bmp, webp)"
        )
    
    if not validate_image_file(model_image):
        raise HTTPException(
            status_code=400, 
            detail="Model image must be a valid image file (jpg, jpeg, png, gif, bmp, webp)"
        )
    
    # Generate unique filenames for temp files
    session_id = str(uuid.uuid4())
    clothing_ext = Path(clothing_image.filename).suffix
    model_ext = Path(model_image.filename).suffix
    
    clothing_temp_path = UPLOAD_DIR / f"clothing_{session_id}{clothing_ext}"
    model_temp_path = UPLOAD_DIR / f"model_{session_id}{model_ext}"
    
    # Generate output filename
    if not output_filename:
        output_filename = f"product_listing_{session_id}.png"
    elif not output_filename.endswith(('.png', '.jpg', '.jpeg')):
        output_filename += ".png"
    
    output_path = OUTPUT_DIR / output_filename
    
    try:
        # Save uploaded files temporarily
        print(f"📁 Saving clothing image: {clothing_image.filename} -> {clothing_temp_path}")
        save_upload_file(clothing_image, clothing_temp_path)
        print(f"📁 Saving model image: {model_image.filename} -> {model_temp_path}")
        save_upload_file(model_image, model_temp_path)
        
        # Step 1: Analyze the clothing item
        try:
            clothing_analysis = analyze_clothing(str(clothing_temp_path))
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to analyze clothing item: {str(e)}"
            )
        
        # Step 2: Generate the product listing image
        try:
            success = generate(
                str(clothing_temp_path), 
                str(model_temp_path), 
                str(output_path)
            )
            
            if not success:
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to generate product listing image"
                )
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to generate product listing: {str(e)}"
            )
        
        # Generate image URL for frontend access
        image_url = f"/images/{output_filename}"
        
        return ProductListingResponse(
            success=True,
            message="Product listing generated successfully!",
            clothing_analysis=clothing_analysis,
            generated_image_url=image_url,
            generated_image_path=str(output_path)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected error: {str(e)}"
        )
    finally:
        # Clean up temporary files
        cleanup_temp_files(clothing_temp_path, model_temp_path)

@app.get("/images/{filename}")
async def get_image(filename: str):
    """Serve generated images"""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "endpoints": {
            "generate": "/generate-product-listing",
            "images": "/images/{filename}",
            "health": "/health"
        },
        "upload_dir": str(UPLOAD_DIR),
        "output_dir": str(OUTPUT_DIR)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
