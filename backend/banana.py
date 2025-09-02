# To run this code you need to install the following dependencies:
# pip install google-genai pillow

import base64
import mimetypes
import os
import argparse
import sys
import json
from typing import List
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv()


class ClothingAnalysis(BaseModel):
    """Structured output for clothing item analysis"""
    description: str
    tags: List[str]
    
    def display(self):
        """Pretty print the analysis results"""
        print("\n" + "="*50)
        print("🔍 CLOTHING ANALYSIS RESULTS")
        print("="*50)
        print(f"📝 Description: {self.description}")
        print(f"🏷️  Tags: {', '.join(self.tags)}")
        print("="*50 + "\n")


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to: {file_name}")


def parse_arguments():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set default paths
    default_clothing = os.path.join(script_dir, 'clothes', 'IMG_7277.jpeg')
    default_model = os.path.join(script_dir, 'model', 'ImageCrocPrototype.jpeg')
    default_output_dir = os.path.join(script_dir, 'output')
    default_output = os.path.join(default_output_dir, 'product_listing.png')
    
    parser = argparse.ArgumentParser(description='Generate product listing images of a model wearing clothing')
    parser.add_argument('--clothing', default=default_clothing, help=f'Path to the clothing image (default: {default_clothing})')
    parser.add_argument('--model', default=default_model, help=f'Path to the model image (default: {default_model})')
    parser.add_argument('--output', default=default_output, help=f'Output filename for the generated image (default: {default_output})')
    return parser.parse_args()


def load_image(image_path):
    """Load and validate image file"""
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        image = Image.open(image_path)
        return image
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        sys.exit(1)


def analyze_clothing(clothing_image_path):
    """Analyze clothing item and return structured information"""
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )
    
    # Load the clothing image
    clothing_image = load_image(clothing_image_path)
    
    analysis_prompt = """Analyze this clothing item and provide a detailed analysis in JSON format with the following structure:

{
  "description": "A detailed description of the clothing item including style, design, and notable features",
  "tags": ["list", "of", "relevant", "tags", "about", "color", "texture", "type", "style", "etc"]
}

For the tags, include relevant characteristics such as:
- Type of clothing (e.g. "hat", "shirt", "dress", "jacket")
- Color(s) (e.g. "brown", "black", "multicolor")
- Material/texture (e.g. "cotton", "denim", "leather", "straw", "woven")
- Style (e.g. "casual", "formal", "vintage", "modern")
- Notable features (e.g. "wide-brim", "button-up", "sleeveless", "patterned")
- Fit (e.g. "loose", "fitted", "oversized")

Provide only the JSON response, no additional text."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[analysis_prompt, clothing_image],
        )
        
        # Parse the JSON response
        json_text = response.text.strip()
        if json_text.startswith('```json'):
            json_text = json_text[7:-3].strip()
        elif json_text.startswith('```'):
            json_text = json_text[3:-3].strip()
            
        analysis_data = json.loads(json_text)
        return ClothingAnalysis(**analysis_data)
        
    except json.JSONDecodeError as e:
        print(f"Error parsing analysis response: {e}")
        print(f"Raw response: {response.text}")
        # Fallback analysis
        return ClothingAnalysis(
            description="Analysis failed - could not parse response",
            tags=["analysis-failed"]
        )
    except Exception as e:
        print(f"Error analyzing clothing: {e}")
        # Fallback analysis
        return ClothingAnalysis(
            description="Analysis failed due to error",
            tags=["analysis-error"]
        )


def generate(clothing_image_path, model_image_path, output_filename):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    # Ensure output directory exists
    output_dir = os.path.dirname(output_filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # Load the input images
    clothing_image = load_image(clothing_image_path)
    model_image = load_image(model_image_path)
    
    print(f"📷 Loaded clothing image: {clothing_image_path} ({clothing_image.size})")
    print(f"👤 Loaded model image: {model_image_path} ({model_image.size})")

    model = "gemini-2.5-flash-image-preview"
    
    prompt = """Create a sharp, high-quality image with four quadrants showing the person from the first image wearing the exact clothing item from the second image. Requirements:

1. Each quadrant shows a different angle (front, back, left side, right side)
2. The clothing must match EXACTLY: same color, texture, fit, and all details from the product image
3. Sharp focus with close-up view to clearly showcase the clothing
4. Consistent lighting and background across all quadrants
5. The clothing should fit naturally and realistically on the person
6. Maintain the exact fabric appearance, stitching, logos, and design elements
7. Professional photo quality suitable for online clothing marketplace
"""

    # Order: prompt, model_image (person - first), clothing_image (clothing - second)
    contents = [prompt, model_image, clothing_image]
    generate_content_config = types.GenerateContentConfig(
        response_modalities=[
            "IMAGE",
            "TEXT",
        ],
    )

    try:
        # Use non-streaming generation for single image output
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )
        
        # Process the response parts
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print("Generated text:", part.text)
            elif part.inline_data is not None:
                # Save the generated image
                image = Image.open(BytesIO(part.inline_data.data))
                image.save(output_filename)
                print(f"Product listing image saved to: {output_filename}")
                return True
                
        print("No image was generated in the response")
        return False
        
    except Exception as e:
        print(f"Error generating content: {e}")
        return False

if __name__ == "__main__":
    args = parse_arguments()
    
    print(f"Loading clothing image: {args.clothing}")
    print(f"Loading model image: {args.model}")
    print(f"Output will be saved to: {args.output}")
    
    # Step 1: Analyze the clothing item
    print("\n🔍 Analyzing clothing item...")
    clothing_analysis = analyze_clothing(args.clothing)
    clothing_analysis.display()
    
    # Step 2: Generate the product listing image
    print("🎨 Generating product listing image...")
    success = generate(args.clothing, args.model, args.output)
    
    if success:
        print("✓ Product listing image generated successfully!")
        print(f"📁 Image saved at: {args.output}")
        
        # Summary
        print("\n📋 WORKFLOW COMPLETE:")
        print(f"   • Clothing analyzed: {clothing_analysis.description[:50]}...")
        print(f"   • Tags identified: {len(clothing_analysis.tags)} tags")
        print(f"   • Product image: Generated successfully")
    else:
        print("✗ Failed to generate product listing image")
        sys.exit(1)
