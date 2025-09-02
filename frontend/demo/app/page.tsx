"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Upload, Play, ImageIcon, User, Sparkles, AlertCircle } from "lucide-react"
import { useProductStore, type ProductCard } from "@/lib/stores"

export default function AIProductCardGenerator() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [clothingImage, setClothingImage] = useState<File | null>(null)
  const [modelImage, setModelImage] = useState<File | null>(null)
  
  // Use the store instead of local state
  const { isGenerating, generatedCards, error, generateProductCard, clearCards, setError } = useProductStore()

  const handleClothingUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setClothingImage(e.target.files[0])
    }
  }

  const handleModelUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setModelImage(e.target.files[0])
    }
  }

  const handleGenerateWithAI = async () => {
    if (!clothingImage || !modelImage) return
    
    setIsModalOpen(false)
    setError(null)
    
    // Generate unique filename
    const timestamp = Date.now()
    const outputFilename = `product_listing_${timestamp}.png`
    
    await generateProductCard(clothingImage, modelImage, outputFilename)
    
    // Clear the uploaded files after generation
    setClothingImage(null)
    setModelImage(null)
  }

  const handleDismissError = () => {
    setError(null)
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-6 py-4">
          <h1 className="text-2xl font-semibold text-foreground">AI Product Card Generator</h1>
          <p className="text-muted-foreground mt-1">Create stunning product cards with AI-generated content</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-12">
        {/* Upload Section */}
        <div className="text-center mb-16">
          <div className="max-w-2xl mx-auto">
            <h2 className="text-4xl font-bold text-foreground mb-6 text-balance">Transform Your Products with AI</h2>
            <p className="text-lg text-muted-foreground mb-12 text-pretty">
              Upload your clothing and model images to generate professional product cards with AI-powered descriptions
              and styling.
            </p>

            <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
              <DialogTrigger asChild>
                <Button size="lg" className="px-8 py-6 text-lg font-medium">
                  <Upload className="mr-2 h-5 w-5" />
                  Upload Images & Generate
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle className="text-xl font-semibold">Upload Your Images</DialogTitle>
                </DialogHeader>
                <div className="space-y-6 py-4">
                  {/* Clothing Image Upload */}
                  <div className="space-y-2">
                    <Label htmlFor="clothing" className="text-sm font-medium flex items-center">
                      <ImageIcon className="mr-2 h-4 w-4" />
                      Clothing/Product Image
                    </Label>
                    <Input
                      id="clothing"
                      type="file"
                      accept="image/*"
                      onChange={handleClothingUpload}
                      className="cursor-pointer"
                    />
                    {clothingImage && (
                      <div className="flex items-center space-x-2">
                        <p className="text-xs text-muted-foreground">Selected: {clothingImage.name}</p>
                        <img 
                          src={URL.createObjectURL(clothingImage)} 
                          alt="Clothing preview" 
                          className="w-10 h-10 object-cover rounded border"
                        />
                      </div>
                    )}
                  </div>

                  {/* Model Image Upload */}
                  <div className="space-y-2">
                    <Label htmlFor="model" className="text-sm font-medium flex items-center">
                      <User className="mr-2 h-4 w-4" />
                      Model Image
                    </Label>
                    <Input
                      id="model"
                      type="file"
                      accept="image/*"
                      onChange={handleModelUpload}
                      className="cursor-pointer"
                    />
                    {modelImage && (
                      <div className="flex items-center space-x-2">
                        <p className="text-xs text-muted-foreground">Selected: {modelImage.name}</p>
                        <img 
                          src={URL.createObjectURL(modelImage)} 
                          alt="Model preview" 
                          className="w-10 h-10 object-cover rounded border"
                        />
                      </div>
                    )}
                  </div>

                  <Button
                    onClick={handleGenerateWithAI}
                    disabled={!clothingImage || !modelImage || isGenerating}
                    className="w-full py-3 font-medium"
                  >
                    <Sparkles className="mr-2 h-4 w-4" />
                    {isGenerating ? "Generating..." : "Generate Product Card"}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
            
            {generatedCards.length > 0 && (
              <div className="mt-6">
                <Button 
                  variant="outline" 
                  onClick={clearCards}
                >
                  Clear All Cards
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="max-w-md mx-auto mb-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start">
                <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-red-800 mb-1">Generation Failed</h3>
                  <p className="text-sm text-red-700">{error}</p>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleDismissError}
                    className="mt-2"
                  >
                    Dismiss
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isGenerating && (
          <div className="text-center py-16">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full mb-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
            <h3 className="text-xl font-semibold text-foreground mb-2">Generating Your Product Card</h3>
            <p className="text-muted-foreground">
              AI is analyzing clothing and creating a 4-angle product listing...
            </p>
          </div>
        )}

        {/* Generated Cards */}
        {generatedCards.length > 0 && (
          <div className="space-y-8">
            <div className="text-center">
              <h3 className="text-2xl font-bold text-foreground mb-2">Generated Product Cards</h3>
              <p className="text-muted-foreground">Your AI-generated product cards are ready</p>
            </div>

            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              {generatedCards.map((card) => (
                <Card
                  key={card.id}
                  className="overflow-hidden border-border shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="aspect-square relative bg-secondary/50">
                    <img
                      src={card.modelImage || "/placeholder.svg"}
                      alt="AI-generated 4-angle product listing"
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement
                        target.src = "/placeholder.svg"
                      }}
                    />
                    <div className="absolute top-2 right-2 bg-black/50 text-white text-xs px-2 py-1 rounded">
                      AI Generated
                    </div>
                  </div>
                  <CardContent className="p-6 space-y-4">
                    <div className="space-y-2">
                      <h4 className="text-xl font-semibold text-foreground">{card.productName}</h4>
                      <p className="text-2xl font-bold text-primary">{card.price}</p>
                    </div>

                    <p className="text-sm text-muted-foreground leading-relaxed">{card.description}</p>

                    <div className="flex flex-wrap gap-2">
                      {card.tags.map((tag, index) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {generatedCards.length === 0 && !isGenerating && (
          <div className="text-center py-16">
            <div className="max-w-md mx-auto">
              <div className="w-24 h-24 bg-secondary rounded-full flex items-center justify-center mx-auto mb-6">
                <ImageIcon className="h-12 w-12 text-muted-foreground" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">No Product Cards Yet</h3>
              <p className="text-muted-foreground">Upload your images to get started with AI-generated product cards</p>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
