import { create } from 'zustand'

// Backend API response types
export interface ClothingAnalysis {
  description: string
  tags: string[]
}

export interface ApiResponse {
  success: boolean
  message: string
  clothing_analysis: ClothingAnalysis
  generated_image_url: string
  generated_image_path: string
}

// Frontend ProductCard type (matches page.tsx)
export interface ProductCard {
  id: string
  productName: string
  price: string
  description: string
  tags: string[]
  modelImage: string
  productImage: string
}

// Store state and actions
interface ProductStore {
  // State
  isGenerating: boolean
  generatedCards: ProductCard[]
  error: string | null
  
  // Actions
  generateProductCard: (clothingImage: File, modelImage: File, outputFilename?: string) => Promise<void>
  clearCards: () => void
  setError: (error: string | null) => void
}

// API service function
const generateProductListing = async (
  clothingImage: File, 
  modelImage: File, 
  outputFilename?: string
): Promise<ApiResponse> => {
  const formData = new FormData()
  formData.append('clothing_image', clothingImage)
  formData.append('model_image', modelImage)
  
  if (outputFilename) {
    formData.append('output_filename', outputFilename)
  }
  
  const response = await fetch('http://localhost:8000/generate-product-listing', {
    method: 'POST',
    body: formData,
  })
  
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`API call failed: ${response.status} ${response.statusText} - ${errorText}`)
  }
  
  return response.json()
}

// Helper function to extract product name from description
const extractProductName = (description: string): string => {
  // Extract the main item type from the description
  const firstSentence = description.split('.')[0]
  
  // Common patterns to extract product names
  if (firstSentence.toLowerCase().includes('hat')) {
    return 'Premium Straw Hat'
  } else if (firstSentence.toLowerCase().includes('shirt')) {
    return 'Designer Shirt'
  } else if (firstSentence.toLowerCase().includes('dress')) {
    return 'Elegant Dress'
  } else if (firstSentence.toLowerCase().includes('jacket')) {
    return 'Stylish Jacket'
  } else {
    // Default: capitalize first few words
    const words = firstSentence.split(' ').slice(0, 3)
    return words.map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
  }
}

// Helper function to generate price based on item type and tags
const generatePrice = (description: string, tags: string[]): string => {
  const desc = description.toLowerCase()
  const tagList = tags.map(tag => tag.toLowerCase())
  
  // Base price logic
  let basePrice = 50
  
  if (desc.includes('hat')) basePrice = 45
  if (desc.includes('premium') || desc.includes('classic')) basePrice += 20
  if (tagList.includes('luxury') || tagList.includes('designer')) basePrice += 30
  if (tagList.includes('handmade') || tagList.includes('artisan')) basePrice += 25
  if (desc.includes('straw') && desc.includes('wide-brim')) basePrice += 15
  
  // Add some randomness
  const variation = Math.floor(Math.random() * 20) - 10
  const finalPrice = Math.max(basePrice + variation, 25)
  
  return `$${finalPrice}.00`
}

// Helper function to map API response to ProductCard
const mapApiResponseToProductCard = (apiResponse: ApiResponse): ProductCard => {
  const { clothing_analysis, generated_image_url } = apiResponse
  
  return {
    id: Date.now().toString(),
    productName: extractProductName(clothing_analysis.description),
    price: generatePrice(clothing_analysis.description, clothing_analysis.tags),
    description: clothing_analysis.description,
    tags: clothing_analysis.tags,
    modelImage: `http://localhost:8000${generated_image_url}`, // Full URL for the generated 4-angle image
    productImage: `http://localhost:8000${generated_image_url}`, // Same as model image for now
  }
}

// Create the Zustand store
export const useProductStore = create<ProductStore>((set, get) => ({
  // Initial state
  isGenerating: false,
  generatedCards: [],
  error: null,
  
  // Actions
  generateProductCard: async (clothingImage: File, modelImage: File, outputFilename?: string) => {
    set({ isGenerating: true, error: null })
    
    try {
      // Validate files
      if (!clothingImage || !modelImage) {
        throw new Error('Both clothing and model images are required')
      }
      
      // Validate file types
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/webp']
      if (!allowedTypes.includes(clothingImage.type)) {
        throw new Error('Clothing image must be a valid image file (jpg, jpeg, png, gif, bmp, webp)')
      }
      if (!allowedTypes.includes(modelImage.type)) {
        throw new Error('Model image must be a valid image file (jpg, jpeg, png, gif, bmp, webp)')
      }
      
      // Call the backend API with file uploads
      const apiResponse = await generateProductListing(clothingImage, modelImage, outputFilename)
      
      // Map the response to our ProductCard format
      const newCard = mapApiResponseToProductCard(apiResponse)
      
      // Add the new card to the beginning of the array
      set(state => ({
        generatedCards: [newCard, ...state.generatedCards],
        isGenerating: false,
        error: null
      }))
      
    } catch (error) {
      console.error('Failed to generate product card:', error)
      set({
        isGenerating: false,
        error: error instanceof Error ? error.message : 'Failed to generate product card'
      })
    }
  },
  
  clearCards: () => {
    set({ generatedCards: [], error: null })
  },
  
  setError: (error: string | null) => {
    set({ error })
  }
}))
